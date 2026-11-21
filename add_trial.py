"""
Add Experimental Trial Module for Streamlit UI.

Allows scientific researchers to enter new biodegradation experiments with
automatic real-time calculation of weight loss percentages, daily rates,
surface-area normalized rates, and evidence quality classification.
"""

import streamlit as st
from database import db_manager
from calculations import (
    calculate_weight_loss,
    calculate_daily_rate,
    calculate_surface_normalized_rate,
    classify_evidence_quality,
    validate_trial_inputs
)
from modules.evidence_quality import render_evidence_badge
from config import TARGET_PLASTICS, RECOGNIZED_STANDARDS


def render_add_trial_page():
    """Render the trial input form with live calculation previews."""
    st.markdown("## 🧪 Add New Experimental Trial")
    st.markdown(
        "Enter published experimental biodegradation parameters. Calculated rates and evidence "
        "quality are determined automatically from reported analytical methods."
    )

    with st.form("add_trial_form", clear_on_submit=False):
        # ------------------------------------------------------------
        # Section 1: Polymer Substrate
        # ------------------------------------------------------------
        st.markdown("### 1. Polymer Substrate Information")
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            plastic_abbrev = st.selectbox(
                "Plastic Polymer *",
                options=[p["abbreviation"] for p in TARGET_PLASTICS],
                format_func=lambda x: f"{x} – {next(p['name'] for p in TARGET_PLASTICS if p['abbreviation'] == x)}"
            )
        with p_col2:
            matched_plastic = next(p for p in TARGET_PLASTICS if p["abbreviation"] == plastic_abbrev)
            st.info(f"**Category:** {matched_plastic['category']}\n\n{matched_plastic['description']}")

        # ------------------------------------------------------------
        # Section 2: Microorganism & Biological Agent
        # ------------------------------------------------------------
        st.markdown("### 2. Biological Agent / Microorganism")
        org_col1, org_col2, org_col3 = st.columns(3)
        with org_col1:
            organism_name = st.text_input("Organism Name *", placeholder="e.g. Ideonella sakaiensis")
        with org_col2:
            organism_type = st.selectbox(
                "Organism Type *",
                options=["Bacteria", "Fungi", "Consortium", "Enzyme/Cell-free"]
            )
        with org_col3:
            strain_id = st.text_input("Strain ID / Identifier", placeholder="e.g. 201-F6 or DSM 43793")

        org_sub1, org_sub2 = st.columns(2)
        with org_sub1:
            culture_source = st.text_input(
                "Culture Collection / Isolation Source",
                placeholder="e.g. ATCC 15692, DSMZ, or isolated from soil"
            )
        with org_sub2:
            enzyme_info = st.text_input(
                "Enzyme / Pathway Information",
                placeholder="e.g. PETase (ISF6_4831), Cutinase, Alkane hydroxylase"
            )

        # ------------------------------------------------------------
        # Section 3: Experimental & Environmental Conditions
        # ------------------------------------------------------------
        st.markdown("### 3. Incubation & Environmental Conditions")
        cond1, cond2, cond3 = st.columns(3)
        with cond1:
            temperature = st.number_input("Temperature (°C) *", min_value=-10.0, max_value=100.0, value=30.0, step=0.5)
        with cond2:
            ph_val = st.number_input("pH *", min_value=1.0, max_value=14.0, value=7.0, step=0.1)
        with cond3:
            duration_days = st.number_input("Incubation Duration (Days) *", min_value=0.1, max_value=1000.0, value=30.0, step=1.0)

        cond4, cond5, cond6 = st.columns(3)
        with cond4:
            pretreatment = st.selectbox(
                "Pretreatment Method",
                options=[
                    "None",
                    "UV photo-oxidation (UVA/UVB)",
                    "Thermal aging / Heat",
                    "Chemical oxidation (HNO3 / Fenton)",
                    "Gamma irradiation",
                    "Mechanical grinding / Cryomilling",
                    "Chemical pyrolysis to oil"
                ]
            )
        with cond5:
            incubation_method = st.selectbox(
                "Incubation System",
                options=[
                    "Liquid culture shake flask",
                    "Soil burial microcosm",
                    "Controlled composting reactor",
                    "Agar solid surface culture",
                    "Seawater / Marine aquarium",
                    "In vivo insect gut feeding trial",
                    "In vitro enzyme buffer solution"
                ]
            )
        with cond6:
            medium_used = st.text_input(
                "Medium / Substrate Used",
                value="Mineral Salt Medium (MSM)"
            )

        # ------------------------------------------------------------
        # Section 4: Quantitative Measurements
        # ------------------------------------------------------------
        st.markdown("### 4. Gravimetric Measurements & Surface Geometry")
        meas1, meas2, meas3 = st.columns(3)
        with meas1:
            initial_weight = st.number_input(
                "Initial Weight (mg) *",
                min_value=0.1,
                max_value=100000.0,
                value=50.0,
                step=1.0
            )
        with meas2:
            final_weight = st.number_input(
                "Final Weight (mg) *",
                min_value=0.0,
                max_value=100000.0,
                value=42.0,
                step=1.0
            )
        with meas3:
            surface_area = st.number_input(
                "Geometric Surface Area (cm²)",
                min_value=0.0,
                max_value=1000.0,
                value=4.0,
                step=0.1,
                help="Optional. Leave 0.0 if not reported in paper."
            )

        # ------------------------------------------------------------
        # Section 5: Analytical Confirmation & Standards
        # ------------------------------------------------------------
        st.markdown("### 5. Analytical Confirmation & Standards Compliance")
        conf1, conf2 = st.columns(2)
        with conf1:
            analytical_methods = st.text_input(
                "Analytical Confirmation Techniques *",
                value="FTIR + SEM",
                help="e.g. FTIR + SEM, GPC + HPLC, NMR, Weight loss only. Multiple methods determine HIGH evidence quality."
            )
        with conf2:
            data_source = st.selectbox(
                "Data Source Category *",
                options=["Verified Literature", "Illustrative Demo"],
                help="Indicate whether this record is extracted from peer-reviewed literature or is for demonstration."
            )

        std1, std2, std3 = st.columns(3)
        with std1:
            standard_name = st.selectbox(
                "Testing Standard Framework",
                options=["None", "ASTM", "ISO", "Not reported"]
            )
        with std2:
            standard_number = st.selectbox(
                "Standard Specification",
                options=RECOGNIZED_STANDARDS
            )
        with std3:
            standard_followed = st.selectbox(
                "Standard Formally Followed?",
                options=["No", "Yes", "Not reported"]
            )

        # ------------------------------------------------------------
        # Section 6: Research Citation & DOI
        # ------------------------------------------------------------
        st.markdown("### 6. Research Publication Reference")
        pub1, pub2 = st.columns([3, 1])
        with pub1:
            publication_reference = st.text_area(
                "Full Publication Citation *",
                placeholder="Author(s), Year, Title, Journal Name, Volume(Issue), Pages"
            )
        with pub2:
            publication_year = st.number_input("Publication Year", min_value=1950, max_value=2030, value=2024)

        obs = st.text_area("Additional Experimental Observations & Notes", placeholder="e.g. Specific monomer yields, biofilm thickness, enzyme kinetics")

        # ------------------------------------------------------------
        # Live Calculation Preview
        # ------------------------------------------------------------
        st.markdown("---")
        st.markdown("#### ⚡ Live Calculated Rates Preview")

        calc_w_loss, w_warn = calculate_weight_loss(initial_weight, final_weight)
        calc_daily_rate, d_warn = calculate_daily_rate(calc_w_loss, duration_days)
        actual_area = surface_area if surface_area > 0 else None
        calc_surf_rate, _ = calculate_surface_normalized_rate(calc_w_loss, duration_days, actual_area)
        calc_evidence = classify_evidence_quality(analytical_methods, data_source)

        c_col1, c_col2, c_col3, c_col4 = st.columns(4)
        with c_col1:
            st.metric("Weight Loss (%)", f"{calc_w_loss:.2f}%" if calc_w_loss is not None else "N/A")
        with c_col2:
            st.metric("Daily Rate (%/day)", f"{calc_daily_rate:.4f}" if calc_daily_rate is not None else "N/A")
        with c_col3:
            st.metric("Surface Rate (%/d/cm²)", f"{calc_surf_rate:.5f}" if calc_surf_rate is not None else "N/A")
        with c_col4:
            st.markdown("**Evidence Quality:**")
            st.markdown(render_evidence_badge(calc_evidence), unsafe_allow_html=True)

        if w_warn:
            st.warning(w_warn)

        # Submit Button
        submitted = st.form_submit_button("💾 Save Experimental Trial to Database", use_container_width=True)

        if submitted:
            # Prepare payload
            payload = {
                "plastic_abbreviation": plastic_abbrev,
                "plastic_name": matched_plastic["name"],
                "polymer_category": matched_plastic["category"],
                "organism_name": organism_name,
                "organism_type": organism_type,
                "strain_id": strain_id or "Unspecified",
                "source_or_culture_collection": culture_source,
                "enzyme_information": enzyme_info,
                "temperature": temperature,
                "pH": ph_val,
                "incubation_duration_days": duration_days,
                "pretreatment_method": pretreatment,
                "incubation_method": incubation_method,
                "medium_used": medium_used,
                "surface_area_cm2": actual_area,
                "initial_weight_mg": initial_weight,
                "final_weight_mg": final_weight,
                "weight_loss_percentage": calc_w_loss,
                "analytical_confirmation": analytical_methods,
                "data_source": data_source,
                "standard_name": standard_name,
                "standard_number": standard_number,
                "standard_followed": standard_followed,
                "evidence_quality": calc_evidence,
                "publication_reference": publication_reference,
                "publication_year": publication_year,
                "additional_observations": obs
            }

            # Attempt database insertion
            success, message, new_id = db_manager.add_trial(payload)
            if success:
                st.success(f"🎉 {message}")
                st.balloons()
            else:
                st.error(f"❌ {message}")
