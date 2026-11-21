"""
Configuration module for the Plastic Biodegradation Trial Database and Analysis System.
Loads environment variables and defines system-wide constants and paths.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the Project
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# MySQL Database Settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "plastic_biodegradation_db")

# Fallback Configuration
USE_SQLITE_FALLBACK = os.getenv("USE_SQLITE_FALLBACK", "True").lower() in ("true", "1", "yes")
SQLITE_DB_PATH = BASE_DIR / os.getenv("SQLITE_DB_PATH", "plastic_biodegradation.db")

# Constructed Database URIs
MYSQL_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
DATABASE_URL = os.getenv("DATABASE_URL", MYSQL_URI)
SQLITE_URI = f"sqlite:///{SQLITE_DB_PATH}"

# Directory Paths
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"
REPORTS_DIR = BASE_DIR / "reports"
SAMPLE_CSV_PATH = DATA_DIR / "sample_trials.csv"
SCHEMA_SQL_PATH = DATABASE_DIR / "schema.sql"

# Ensure runtime directories exist
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Required Plastic Types (6 target polymers)
TARGET_PLASTICS = [
    {
        "abbreviation": "PET",
        "name": "Polyethylene Terephthalate",
        "category": "Synthetic (Aromatic Polyester)",
        "description": "Thermoplastic polymer widely used in beverage bottles, food containers, and synthetic fibers. Chemically recalcitrant due to aromatic rings, but enzymatically hydrolyzable by cutinases and PETases."
    },
    {
        "abbreviation": "PE",
        "name": "Polyethylene",
        "category": "Synthetic (Polyolefin)",
        "description": "High-density (HDPE) or low-density (LDPE) polymer with a high molecular weight carbon-carbon backbone. Highly resistant to microbial attack without oxidative pretreatment."
    },
    {
        "abbreviation": "PP",
        "name": "Polypropylene",
        "category": "Synthetic (Polyolefin)",
        "description": "Semicrystalline polyolefin with repeating propylene units and methyl side groups. Exhibits high chemical resistance and hydrophobicity, degrading slowly under biotic conditions."
    },
    {
        "abbreviation": "PS",
        "name": "Polystyrene",
        "category": "Synthetic (Aromatic Polyolefin)",
        "description": "Aromatic polymer derived from styrene monomer. Widely used in packaging and disposable cutlery. Ring-cleaving bacteria and insect gut microbiomes show partial degradation capabilities."
    },
    {
        "abbreviation": "PLA",
        "name": "Polylactic Acid",
        "category": "Bio-based (Aliphatic Polyester)",
        "description": "Biodegradable thermoplastic synthesized from renewable fermented plant starch (lactic acid). Readily degraded under industrial thermophilic composting conditions (>58°C)."
    },
    {
        "abbreviation": "PHA",
        "name": "Polyhydroxyalkanoates",
        "category": "Bio-based (Microbial Polyester)",
        "description": "Natural intracellular storage biopolyesters accumulated by various bacteria. Rapidly biodegradable in soil, marine, and composting environments by extracellular PHA depolymerases."
    }
]

# Evidence Quality Definitions
EVIDENCE_LEVELS = {
    "HIGH": {
        "color": "#28a745",
        "bg_color": "#d4edda",
        "badge_class": "badge-high",
        "description": "Multiple analytical techniques (e.g. FTIR + SEM, FTIR + GPC, NMR) verifying polymer chain cleavage."
    },
    "MODERATE": {
        "color": "#17a2b8",
        "bg_color": "#d1ecf1",
        "badge_class": "badge-moderate",
        "description": "Single analytical confirmation method (e.g. FTIR alone or SEM alone)."
    },
    "LOW": {
        "color": "#fd7e14",
        "bg_color": "#ffeeba",
        "badge_class": "badge-low",
        "description": "Weight loss or visual observation alone without complementary spectroscopic/chromatographic confirmation."
    },
    "UNVERIFIED": {
        "color": "#6c757d",
        "bg_color": "#e2e3e5",
        "badge_class": "badge-unverified",
        "description": "Source or experimental evidence is preliminary or lacks sufficient analytical verification."
    }
}

# Standard Reference Standards Catalog
RECOGNIZED_STANDARDS = [
    "ASTM D5988 (Aerobic biodegradation in soil)",
    "ASTM D5338 (Aerobic biodegradation under controlled composting)",
    "ASTM D6400 (Compostable plastics specification)",
    "ASTM D5210 (Anaerobic biodegradation in sewage sludge)",
    "ISO 14855 (Controlled composting test)",
    "ISO 17556 (Soil respirometric biodegradation)",
    "ISO 14852 (Aqueous medium aerobic biodegradation)",
    "ISO 14851 (Aqueous medium closed respirometer)",
    "None / Custom Academic Method",
    "Not reported in publication"
]
