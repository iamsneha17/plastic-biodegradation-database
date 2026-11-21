"""
Calculations Module for Plastic Biodegradation Trial Database.

Provides strictly validated scientific formulas:
A. Weight loss percentage
B. Normalized degradation rate (%/day)
C. Surface-area normalized degradation rate (%/day/cm2)
D. Analytical evidence quality classification
E. Input validation and sanity checks
"""

import math
from typing import Optional, Dict, Any, Tuple


def calculate_weight_loss(
    initial_weight_mg: Optional[float], 
    final_weight_mg: Optional[float]
) -> Tuple[Optional[float], Optional[str]]:
    """
    Calculate the gravimetric weight loss percentage:
    Weight Loss (%) = ((Initial Weight - Final Weight) / Initial Weight) * 100

    Args:
        initial_weight_mg: Starting mass in milligrams (must be > 0)
        final_weight_mg: Mass after incubation in milligrams (must be >= 0)

    Returns:
        Tuple of (weight_loss_percentage, warning_or_error_message)
    """
    if initial_weight_mg is None or final_weight_mg is None:
        return None, "Both initial and final weights are required for weight loss calculation."
    
    try:
        initial = float(initial_weight_mg)
        final = float(final_weight_mg)
    except (ValueError, TypeError):
        return None, "Invalid numerical value provided for weight measurement."

    if initial <= 0:
        return None, "Initial weight must be strictly positive (> 0 mg)."

    if final < 0:
        return None, "Final weight cannot be negative."

    diff = initial - final
    loss_pct = (diff / initial) * 100.0

    warning = None
    if loss_pct < 0:
        warning = (
            f"Negative weight loss ({loss_pct:.2f}%) indicates mass gain, "
            "often attributable to microbial biomass/biofilm accumulation or moisture absorption."
        )
    elif loss_pct > 100:
        warning = (
            f"Calculated weight loss ({loss_pct:.2f}%) exceeds 100%, "
            "which represents physically impossible polymer mass disappearance."
        )

    return round(loss_pct, 4), warning


def calculate_daily_rate(
    weight_loss_pct: Optional[float], 
    duration_days: Optional[float]
) -> Tuple[Optional[float], Optional[str]]:
    """
    Calculate the daily normalized degradation rate:
    Degradation Rate (%/day) = Weight Loss Percentage / Incubation Duration in Days

    Args:
        weight_loss_pct: Weight loss percentage (%)
        duration_days: Incubation duration in days (must be > 0)

    Returns:
        Tuple of (rate_pct_per_day, warning_or_error_message)
    """
    if weight_loss_pct is None:
        return None, "Weight loss percentage is missing."
    if duration_days is None:
        return None, "Incubation duration is missing."

    try:
        loss = float(weight_loss_pct)
        days = float(duration_days)
    except (ValueError, TypeError):
        return None, "Invalid numerical value provided for rate calculation."

    if days <= 0:
        return None, "Incubation duration must be strictly greater than 0 days to avoid division by zero."

    rate = loss / days
    return round(rate, 5), None


def calculate_surface_normalized_rate(
    weight_loss_pct: Optional[float],
    duration_days: Optional[float],
    surface_area_cm2: Optional[float]
) -> Tuple[Optional[float], Optional[str]]:
    """
    Calculate the surface-area normalized degradation rate:
    Normalized Rate = Weight Loss Percentage / (Incubation Duration in Days * Surface Area in cm2)

    Note: This rate must be interpreted with caution. Polymer film thickness,
    crystallinity, surface roughness, and bacterial attachment density influence
    observed kinetics.

    Args:
        weight_loss_pct: Weight loss percentage (%)
        duration_days: Incubation period in days
        surface_area_cm2: Geometric surface area in cm2

    Returns:
        Tuple of (normalized_rate, warning_or_error_message)
    """
    if surface_area_cm2 is None:
        return None, "Surface area not provided; surface-normalized rate cannot be computed."

    try:
        area = float(surface_area_cm2)
    except (ValueError, TypeError):
        return None, "Invalid numerical surface area value."

    if area <= 0:
        return None, "Surface area must be strictly positive (> 0 cm2)."

    daily_rate, err = calculate_daily_rate(weight_loss_pct, duration_days)
    if err or daily_rate is None:
        return None, err

    norm_rate = daily_rate / area
    return round(norm_rate, 6), None


def classify_evidence_quality(
    analytical_confirmation: Optional[str],
    data_source: Optional[str] = "Verified Literature"
) -> str:
    """
    Classify the scientific evidence quality of a biodegradation trial.
    
    Categories:
    - HIGH: Multiple analytical techniques (e.g. FTIR + SEM, FTIR + GPC, NMR + SEM, GC-MS + FTIR)
    - MODERATE: Single analytical confirmation method (e.g. FTIR, SEM, GPC, or GC-MS alone)
    - LOW: Weight loss or visual observation only without spectroscopic/chromatographic confirmation
    - UNVERIFIED: Source is preliminary, unverified, or ambiguous

    Note: This classification reflects analytical rigor and is completely independent
    of whether an ASTM/ISO standard was formally followed.
    """
    if not analytical_confirmation or not str(analytical_confirmation).strip():
        return "UNVERIFIED"

    text = str(analytical_confirmation).strip().upper()
    source_text = str(data_source).strip().upper() if data_source else ""

    if "UNVERIFIED" in source_text or "PRELIMINARY" in text:
        return "UNVERIFIED"

    # Known analytical methods
    methods = [
        "FTIR", "SEM", "GPC", "SEC", "NMR", "GC-MS", "LC-MS", 
        "XPS", "XRD", "DSC", "TGA", "AFM", "CO2 RESPIROMETRY", "STURM TEST"
    ]

    detected_methods = [m for m in methods if m in text]
    
    # Check for compound conjunctions like "FTIR + SEM", "SEM AND GPC", "FTIR, SEM"
    has_multiple_markers = (
        len(detected_methods) >= 2 or
        "+" in text or
        " AND " in text or
        "&" in text or
        "MULTIPLE" in text or
        "," in text
    )

    if has_multiple_markers and len(detected_methods) >= 2:
        return "HIGH"
    elif len(detected_methods) >= 1:
        return "MODERATE"
    elif any(term in text for term in ["WEIGHT LOSS ONLY", "VISUAL", "CLEARING ZONE", "TURBIDITY", "GRAVIMETRIC"]):
        return "LOW"
    else:
        return "MODERATE" if len(text) > 3 else "UNVERIFIED"


def validate_trial_inputs(data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """
    Validate all inputs before storing a trial record.

    Returns:
        (is_valid, error_dict)
    """
    errors: Dict[str, str] = {}

    # Plastic validation
    plastic = data.get("plastic_abbreviation")
    allowed_plastics = ["PET", "PE", "PP", "PS", "PLA", "PHA"]
    if not plastic or plastic.upper() not in allowed_plastics:
        errors["plastic_abbreviation"] = f"Plastic must be one of: {', '.join(allowed_plastics)}."

    # Organism validation
    organism_name = str(data.get("organism_name", "")).strip()
    if not organism_name or len(organism_name) < 2:
        errors["organism_name"] = "Organism name is required (minimum 2 characters)."

    # Organism Type validation
    organism_type = data.get("organism_type")
    allowed_types = ["Bacteria", "Fungi", "Consortium", "Enzyme/Cell-free"]
    if organism_type and organism_type not in allowed_types:
        errors["organism_type"] = f"Organism type must be one of: {', '.join(allowed_types)}."

    # Temperature validation (-10°C to 100°C)
    temp = data.get("temperature")
    if temp is None:
        errors["temperature"] = "Incubation temperature is required."
    else:
        try:
            t = float(temp)
            if not (-10.0 <= t <= 100.0):
                errors["temperature"] = "Temperature must be between -10°C and 100°C."
        except ValueError:
            errors["temperature"] = "Temperature must be a valid number."

    # pH validation (1.0 to 14.0)
    ph = data.get("pH")
    if ph is None:
        errors["pH"] = "pH value is required."
    else:
        try:
            p = float(ph)
            if not (1.0 <= p <= 14.0):
                errors["pH"] = "pH must be between 1.0 and 14.0."
        except ValueError:
            errors["pH"] = "pH must be a valid number."

    # Incubation duration validation (> 0 days)
    duration = data.get("incubation_duration_days")
    if duration is None:
        errors["incubation_duration_days"] = "Incubation duration is required."
    else:
        try:
            d = float(duration)
            if d <= 0:
                errors["incubation_duration_days"] = "Incubation duration must be strictly positive (> 0 days)."
        except ValueError:
            errors["incubation_duration_days"] = "Duration must be a valid number."

    # Initial and Final weight validation
    init_w = data.get("initial_weight_mg")
    fin_w = data.get("final_weight_mg")
    w_loss = data.get("weight_loss_percentage")

    if init_w is not None and fin_w is not None:
        try:
            i_val = float(init_w)
            f_val = float(fin_w)
            if i_val <= 0:
                errors["initial_weight_mg"] = "Initial weight must be > 0 mg."
            if f_val < 0:
                errors["final_weight_mg"] = "Final weight cannot be negative."
        except ValueError:
            errors["weight"] = "Weights must be numerical values."
    elif w_loss is None:
        errors["weight_loss_percentage"] = "Either Initial/Final weight or explicit Weight Loss (%) is required."

    # Surface area validation (optional, but if provided must be > 0)
    area = data.get("surface_area_cm2")
    if area is not None and str(area).strip() != "":
        try:
            a_val = float(area)
            if a_val <= 0:
                errors["surface_area_cm2"] = "Surface area must be > 0 cm² if provided."
        except ValueError:
            errors["surface_area_cm2"] = "Surface area must be a valid numerical value."

    # Publication Reference
    pub = str(data.get("publication_reference", "")).strip()
    if not pub or len(pub) < 5:
        errors["publication_reference"] = "A valid publication citation or reference is required (min 5 characters)."

    return len(errors) == 0, errors
