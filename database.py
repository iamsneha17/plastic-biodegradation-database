"""
Database Access Layer for Plastic Biodegradation Trial Database.

Handles:
- Relational schema models via SQLAlchemy
- Connection handling with automated graceful SQLite fallback if MySQL is offline
- Database status reporting
- Seed data importation from sample_trials.csv
- Flat denormalized DataFrame queries for Streamlit analytics
- CRUD operations with transaction safety and duplicate detection
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from sqlalchemy import (
    create_engine, Column, Integer, Float, String, Text, ForeignKey,
    DateTime, func, inspect, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, scoped_session
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from config import (
    MYSQL_URI, SQLITE_URI, USE_SQLITE_FALLBACK, DB_NAME, DB_HOST, DB_PORT,
    TARGET_PLASTICS, SAMPLE_CSV_PATH, SCHEMA_SQL_PATH
)
from calculations import (
    calculate_weight_loss, calculate_daily_rate,
    calculate_surface_normalized_rate, classify_evidence_quality,
    validate_trial_inputs
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

# ====================================================================
# SQLAlchemy ORM Models
# ====================================================================

class Plastic(Base):
    __tablename__ = "Plastic"

    plastic_id = Column(Integer, primary_key=True, autoincrement=True)
    plastic_name = Column(String(100), nullable=False)
    plastic_abbreviation = Column(String(20), nullable=False, unique=True, index=True)
    polymer_category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    measurements = relationship("Measurement", back_populates="plastic", cascade="all, delete-orphan")


class Organism(Base):
    __tablename__ = "Organism"

    organism_id = Column(Integer, primary_key=True, autoincrement=True)
    organism_name = Column(String(150), nullable=False, index=True)
    organism_type = Column(String(50), nullable=False, index=True)
    strain_id = Column(String(100), default="Unspecified")
    source_or_culture_collection = Column(String(150), nullable=True)
    enzyme_information = Column(Text, nullable=True)

    measurements = relationship("Measurement", back_populates="organism", cascade="all, delete-orphan")


class ConditionTrial(Base):
    __tablename__ = "Condition_Trial"

    condition_id = Column(Integer, primary_key=True, autoincrement=True)
    temperature = Column(Float, nullable=False)
    pH = Column(Float, nullable=False)
    incubation_duration_days = Column(Float, nullable=False)
    pretreatment_method = Column(String(100), default="None")
    incubation_method = Column(String(100), default="Liquid culture shake flask")
    medium_used = Column(String(150), default="Mineral Salt Medium (MSM)")
    surface_area_cm2 = Column(Float, nullable=True)
    initial_weight_mg = Column(Float, nullable=True)

    measurements = relationship("Measurement", back_populates="condition", cascade="all, delete-orphan")


class Measurement(Base):
    __tablename__ = "Measurement"

    measurement_id = Column(Integer, primary_key=True, autoincrement=True)
    plastic_id = Column(Integer, ForeignKey("Plastic.plastic_id", ondelete="CASCADE"), nullable=False)
    organism_id = Column(Integer, ForeignKey("Organism.organism_id", ondelete="CASCADE"), nullable=False)
    condition_id = Column(Integer, ForeignKey("Condition_Trial.condition_id", ondelete="CASCADE"), nullable=False)
    
    weight_loss_percentage = Column(Float, nullable=False)
    degradation_duration_days = Column(Float, nullable=False)
    analytical_confirmation = Column(String(150), nullable=False)
    percentage_per_day = Column(Float, nullable=False)
    percentage_per_day_per_cm2 = Column(Float, nullable=True)
    publication_reference = Column(Text, nullable=False)
    publication_year = Column(Integer, nullable=True)
    data_source = Column(String(50), default="Verified Literature")
    additional_observations = Column(Text, nullable=True)

    # Relationships
    plastic = relationship("Plastic", back_populates="measurements")
    organism = relationship("Organism", back_populates="measurements")
    condition = relationship("ConditionTrial", back_populates="measurements")
    standards = relationship("StandardFlag", back_populates="measurement", cascade="all, delete-orphan")


class StandardFlag(Base):
    __tablename__ = "Standard_Flag"

    standard_id = Column(Integer, primary_key=True, autoincrement=True)
    measurement_id = Column(Integer, ForeignKey("Measurement.measurement_id", ondelete="CASCADE"), nullable=False)
    standard_name = Column(String(50), default="Not reported")
    standard_number = Column(String(100), default="N/A")
    standard_followed = Column(String(20), default="Not reported")
    evidence_quality = Column(String(30), nullable=False, default="UNVERIFIED")

    measurement = relationship("Measurement", back_populates="standards")


# ====================================================================
# Engine & Session Management
# ====================================================================

class DatabaseManager:
    """Manages database connectivity, schema lifecycle, and queries."""

    def __init__(self):
        self.engine = None
        self.Session = None
        self.engine_type = "unknown"
        self.connection_status = False
        self.error_message = None
        self.initialize_connection()

    def initialize_connection(self):
        """Attempts connection to MySQL; if unavailable and fallback enabled, connects to SQLite."""
        self.error_message = None
        
        # 1. Try MySQL
        try:
            mysql_engine = create_engine(
                MYSQL_URI,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={"connect_timeout": 3}
            )
            # Test ping
            with mysql_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.engine = mysql_engine
            self.engine_type = "MySQL"
            self.connection_status = True
            logger.info("Successfully connected to MySQL database: %s", DB_NAME)
        except Exception as e:
            mysql_err = str(e)
            logger.warning("Could not connect to MySQL (%s). Evaluating fallback.", mysql_err)
            
            if USE_SQLITE_FALLBACK:
                try:
                    sqlite_engine = create_engine(
                        SQLITE_URI,
                        connect_args={"check_same_thread": False}
                    )
                    with sqlite_engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    self.engine = sqlite_engine
                    self.engine_type = "SQLite (Local Fallback)"
                    self.connection_status = True
                    self.error_message = (
                        f"MySQL server at {DB_HOST}:{DB_PORT} was unreachable ({mysql_err[:120]}...). "
                        "Running in standalone SQLite fallback mode so all features remain functional."
                    )
                    logger.info("Operating in standalone SQLite mode: %s", SQLITE_URI)
                except Exception as sqle:
                    self.connection_status = False
                    self.error_message = f"Both MySQL and SQLite failed: {sqle}"
                    logger.error(self.error_message)
            else:
                self.connection_status = False
                self.error_message = f"MySQL connection failed: {mysql_err}"

        if self.engine:
            self.Session = scoped_session(sessionmaker(bind=self.engine))

    def get_status(self) -> Dict[str, Any]:
        """Return connectivity status dictionary."""
        return {
            "is_connected": self.connection_status,
            "engine_type": self.engine_type,
            "database_name": DB_NAME if "MySQL" in self.engine_type else "plastic_biodegradation.db",
            "host": f"{DB_HOST}:{DB_PORT}" if "MySQL" in self.engine_type else "Local Disk",
            "error_message": self.error_message
        }

    def create_schema(self):
        """Create all tables in the active database engine."""
        if not self.engine:
            raise RuntimeError("Database engine not initialized.")
        Base.metadata.create_all(self.engine)
        logger.info("All schema tables successfully verified/created.")

    def seed_target_plastics(self):
        """Ensure all 6 core plastic polymer types are pre-populated."""
        session = self.Session()
        try:
            for p in TARGET_PLASTICS:
                existing = session.query(Plastic).filter_by(plastic_abbreviation=p["abbreviation"]).first()
                if not existing:
                    new_p = Plastic(
                        plastic_name=p["name"],
                        plastic_abbreviation=p["abbreviation"],
                        polymer_category=p["category"],
                        description=p["description"]
                    )
                    session.add(new_p)
            session.commit()
            logger.info("Target plastics verified in database.")
        except Exception as e:
            session.rollback()
            logger.error("Error seeding target plastics: %s", e)
        finally:
            session.close()

    def seed_from_csv(self, csv_path: Optional[str] = None):
        """Seed sample literature records from CSV if Measurement table is empty."""
        target_csv = csv_path or SAMPLE_CSV_PATH
        if not os.path.exists(target_csv):
            logger.warning("Sample CSV file not found at %s. Skipping CSV seed.", target_csv)
            return

        session = self.Session()
        try:
            count = session.query(Measurement).count()
            if count > 0:
                logger.info("Database already contains %d measurement records. Skipping CSV seed.", count)
                return

            df = pd.read_csv(target_csv)
            logger.info("Seeding %d records from %s...", len(df), target_csv)

            for _, row in df.iterrows():
                # 1. Plastic
                abbrev = str(row.get("plastic_abbreviation", "")).strip()
                plastic = session.query(Plastic).filter_by(plastic_abbreviation=abbrev).first()
                if not plastic:
                    plastic = Plastic(
                        plastic_name=str(row.get("plastic_name", abbrev)),
                        plastic_abbreviation=abbrev,
                        polymer_category=str(row.get("polymer_category", "Synthetic")),
                        description=""
                    )
                    session.add(plastic)
                    session.flush()

                # 2. Organism
                org_name = str(row.get("organism_name", "Unknown Organism")).strip()
                strain = str(row.get("strain_id", "Unspecified")).strip()
                organism = session.query(Organism).filter_by(
                    organism_name=org_name,
                    strain_id=strain
                ).first()
                if not organism:
                    organism = Organism(
                        organism_name=org_name,
                        organism_type=str(row.get("organism_type", "Bacteria")),
                        strain_id=strain,
                        source_or_culture_collection=str(row.get("source_or_culture_collection", "")),
                        enzyme_information=str(row.get("enzyme_information", ""))
                    )
                    session.add(organism)
                    session.flush()

                # 3. Condition
                condition = ConditionTrial(
                    temperature=float(row.get("temperature", 30.0)),
                    pH=float(row.get("pH", 7.0)),
                    incubation_duration_days=float(row.get("incubation_duration_days", 30.0)),
                    pretreatment_method=str(row.get("pretreatment_method", "None")),
                    incubation_method=str(row.get("incubation_method", "Liquid culture shake flask")),
                    medium_used=str(row.get("medium_used", "Mineral Salt Medium (MSM)")),
                    surface_area_cm2=float(row["surface_area_cm2"]) if pd.notna(row.get("surface_area_cm2")) else None,
                    initial_weight_mg=float(row["initial_weight_mg"]) if pd.notna(row.get("initial_weight_mg")) else None
                )
                session.add(condition)
                session.flush()

                # 4. Measurement
                w_loss = float(row.get("weight_loss_percentage", 0.0))
                days = float(row.get("incubation_duration_days", 1.0))
                daily_rate, _ = calculate_daily_rate(w_loss, days)
                surf_rate, _ = calculate_surface_normalized_rate(w_loss, days, condition.surface_area_cm2)

                measurement = Measurement(
                    plastic_id=plastic.plastic_id,
                    organism_id=organism.organism_id,
                    condition_id=condition.condition_id,
                    weight_loss_percentage=w_loss,
                    degradation_duration_days=days,
                    analytical_confirmation=str(row.get("analytical_confirmation", "Weight loss only")),
                    percentage_per_day=daily_rate or 0.0,
                    percentage_per_day_per_cm2=surf_rate,
                    publication_reference=str(row.get("publication_reference", "Unspecified Citation")),
                    publication_year=int(row["publication_year"]) if pd.notna(row.get("publication_year")) else None,
                    data_source=str(row.get("data_source", "Verified Literature")),
                    additional_observations=str(row.get("additional_observations", ""))
                )
                session.add(measurement)
                session.flush()

                # 5. Standard_Flag
                ev_quality = str(row.get("evidence_quality", ""))
                if not ev_quality or ev_quality not in ["HIGH", "MODERATE", "LOW", "UNVERIFIED"]:
                    ev_quality = classify_evidence_quality(
                        measurement.analytical_confirmation,
                        measurement.data_source
                    )

                standard_flag = StandardFlag(
                    measurement_id=measurement.measurement_id,
                    standard_name=str(row.get("standard_name", "None")),
                    standard_number=str(row.get("standard_number", "N/A")),
                    standard_followed=str(row.get("standard_followed", "No")),
                    evidence_quality=ev_quality
                )
                session.add(standard_flag)

            session.commit()
            logger.info("Successfully imported all sample trials into the database.")
        except Exception as e:
            session.rollback()
            logger.error("Error during CSV seeding: %s", e)
        finally:
            session.close()

    def get_all_trials_df(self) -> pd.DataFrame:
        """Fetch all trials as a flattened pandas DataFrame for analytics and filtering."""
        if not self.engine:
            return pd.DataFrame()

        sql = """
        SELECT 
            m.measurement_id AS trial_id,
            p.plastic_name,
            p.plastic_abbreviation,
            p.polymer_category,
            o.organism_name,
            o.organism_type,
            o.strain_id,
            o.source_or_culture_collection,
            o.enzyme_information,
            c.temperature,
            c.pH,
            c.incubation_duration_days,
            c.pretreatment_method,
            c.incubation_method,
            c.medium_used,
            c.surface_area_cm2,
            c.initial_weight_mg,
            m.weight_loss_percentage,
            m.degradation_duration_days,
            m.analytical_confirmation,
            m.percentage_per_day,
            m.percentage_per_day_per_cm2,
            m.publication_reference,
            m.publication_year,
            m.data_source,
            m.additional_observations,
            s.standard_name,
            s.standard_number,
            s.standard_followed,
            s.evidence_quality
        FROM Measurement m
        JOIN Plastic p ON m.plastic_id = p.plastic_id
        JOIN Organism o ON m.organism_id = o.organism_id
        JOIN Condition_Trial c ON m.condition_id = c.condition_id
        LEFT JOIN Standard_Flag s ON m.measurement_id = s.measurement_id
        ORDER BY m.measurement_id ASC;
        """
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(text(sql), conn)
            return df
        except Exception as e:
            logger.error("Failed to query trials DataFrame: %s", e)
            return pd.DataFrame()

    def check_duplicate_trial(
        self,
        plastic_abbreviation: str,
        organism_name: str,
        strain_id: str,
        temperature: float,
        duration_days: float,
        pretreatment_method: str
    ) -> bool:
        """Check if an experimental trial with identical key parameters already exists."""
        session = self.Session()
        try:
            exists = (
                session.query(Measurement)
                .join(Plastic, Measurement.plastic_id == Plastic.plastic_id)
                .join(Organism, Measurement.organism_id == Organism.organism_id)
                .join(ConditionTrial, Measurement.condition_id == ConditionTrial.condition_id)
                .filter(
                    Plastic.plastic_abbreviation == plastic_abbreviation,
                    Organism.organism_name.ilike(organism_name.strip()),
                    Organism.strain_id.ilike(strain_id.strip()),
                    ConditionTrial.temperature == temperature,
                    ConditionTrial.incubation_duration_days == duration_days,
                    ConditionTrial.pretreatment_method.ilike(pretreatment_method.strip())
                )
                .first()
            )
            return exists is not None
        finally:
            session.close()

    def add_trial(self, data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """
        Validate and insert a new experimental trial across all 5 relational tables.

        Returns:
            (success, message, new_measurement_id)
        """
        is_valid, errors = validate_trial_inputs(data)
        if not is_valid:
            error_str = " | ".join(f"{k}: {v}" for k, v in errors.items())
            return False, f"Validation Failed: {error_str}", None

        # Check for duplicates
        if self.check_duplicate_trial(
            data["plastic_abbreviation"],
            data["organism_name"],
            data.get("strain_id", "Unspecified"),
            float(data["temperature"]),
            float(data["incubation_duration_days"]),
            data.get("pretreatment_method", "None")
        ):
            return False, "Duplicate record detected: A trial with the same plastic, microorganism, strain, temperature, duration, and pretreatment already exists.", None

        session = self.Session()
        try:
            # 1. Plastic
            plastic = session.query(Plastic).filter_by(
                plastic_abbreviation=data["plastic_abbreviation"]
            ).first()
            if not plastic:
                plastic = Plastic(
                    plastic_name=data.get("plastic_name", data["plastic_abbreviation"]),
                    plastic_abbreviation=data["plastic_abbreviation"],
                    polymer_category=data.get("polymer_category", "Synthetic"),
                    description=data.get("plastic_description", "")
                )
                session.add(plastic)
                session.flush()

            # 2. Organism
            org_name = data["organism_name"].strip()
            strain = data.get("strain_id", "Unspecified").strip()
            organism = session.query(Organism).filter_by(
                organism_name=org_name,
                strain_id=strain
            ).first()
            if not organism:
                organism = Organism(
                    organism_name=org_name,
                    organism_type=data.get("organism_type", "Bacteria"),
                    strain_id=strain,
                    source_or_culture_collection=data.get("source_or_culture_collection", ""),
                    enzyme_information=data.get("enzyme_information", "")
                )
                session.add(organism)
                session.flush()

            # 3. Condition
            surface_area = data.get("surface_area_cm2")
            if surface_area is not None and str(surface_area).strip() != "":
                surface_area = float(surface_area)
            else:
                surface_area = None

            initial_w = data.get("initial_weight_mg")
            if initial_w is not None and str(initial_w).strip() != "":
                initial_w = float(initial_w)
            else:
                initial_w = None

            condition = ConditionTrial(
                temperature=float(data["temperature"]),
                pH=float(data["pH"]),
                incubation_duration_days=float(data["incubation_duration_days"]),
                pretreatment_method=data.get("pretreatment_method", "None"),
                incubation_method=data.get("incubation_method", "Liquid culture shake flask"),
                medium_used=data.get("medium_used", "Mineral Salt Medium (MSM)"),
                surface_area_cm2=surface_area,
                initial_weight_mg=initial_w
            )
            session.add(condition)
            session.flush()

            # 4. Calculations for Measurement
            if "weight_loss_percentage" in data and data["weight_loss_percentage"] is not None:
                w_loss = float(data["weight_loss_percentage"])
            elif initial_w is not None and "final_weight_mg" in data and data["final_weight_mg"] is not None:
                w_loss, _ = calculate_weight_loss(initial_w, float(data["final_weight_mg"]))
                if w_loss is None:
                    w_loss = 0.0
            else:
                w_loss = 0.0

            duration = float(data["incubation_duration_days"])
            daily_rate, _ = calculate_daily_rate(w_loss, duration)
            surf_rate, _ = calculate_surface_normalized_rate(w_loss, duration, surface_area)

            measurement = Measurement(
                plastic_id=plastic.plastic_id,
                organism_id=organism.organism_id,
                condition_id=condition.condition_id,
                weight_loss_percentage=w_loss,
                degradation_duration_days=duration,
                analytical_confirmation=data.get("analytical_confirmation", "Weight loss only"),
                percentage_per_day=daily_rate or 0.0,
                percentage_per_day_per_cm2=surf_rate,
                publication_reference=data["publication_reference"].strip(),
                publication_year=int(data["publication_year"]) if data.get("publication_year") else None,
                data_source=data.get("data_source", "Verified Literature"),
                additional_observations=data.get("additional_observations", "")
            )
            session.add(measurement)
            session.flush()

            # 5. Standard_Flag
            ev_quality = data.get("evidence_quality")
            if not ev_quality or ev_quality not in ["HIGH", "MODERATE", "LOW", "UNVERIFIED"]:
                ev_quality = classify_evidence_quality(
                    measurement.analytical_confirmation,
                    measurement.data_source
                )

            standard_flag = StandardFlag(
                measurement_id=measurement.measurement_id,
                standard_name=data.get("standard_name", "None"),
                standard_number=data.get("standard_number", "N/A"),
                standard_followed=data.get("standard_followed", "No"),
                evidence_quality=ev_quality
            )
            session.add(standard_flag)

            session.commit()
            return True, f"Experimental Trial #{measurement.measurement_id} successfully recorded!", measurement.measurement_id
        except Exception as e:
            session.rollback()
            logger.error("Failed to add trial: %s", e)
            return False, f"Database transaction error: {str(e)}", None
        finally:
            session.close()

    def delete_trial(self, measurement_id: int) -> Tuple[bool, str]:
        """Delete an experimental trial record by ID."""
        session = self.Session()
        try:
            m = session.query(Measurement).filter_by(measurement_id=measurement_id).first()
            if not m:
                return False, f"Trial #{measurement_id} not found."
            session.delete(m)
            session.commit()
            return True, f"Trial #{measurement_id} successfully deleted."
        except Exception as e:
            session.rollback()
            return False, f"Error deleting trial: {str(e)}"
        finally:
            session.close()


# Singleton Instance
db_manager = DatabaseManager()

def init_system_database():
    """Helper to initialize schema and seed initial data."""
    db_manager.create_schema()
    db_manager.seed_target_plastics()
    db_manager.seed_from_csv()
