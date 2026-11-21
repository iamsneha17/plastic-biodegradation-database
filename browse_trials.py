"""
Browse Database Module for Streamlit UI.

Provides rich search, multi-faceted filtering, tabular browsing, and detailed
modal inspections of experimental biodegradation trials.
"""

import streamlit as st
import pandas as pd
from database import db_manager
from data_analysis import filter_trials_dataframe
from modules.evidence_quality import render_evidence_badge, display_evidence_legend


def render_browse_trials_page():
    """Render the Browse Trials page."""
    st.markdown("## 🔍 Browse Biodegradation Database")
    st.markdown(
        "Search and filter experimental records by microorganism, polymer substrate, "
        "analytical evidence quality, or ASTM/ISO testing standard."
    )

    df = db_manager.get_all_trials_df()
    if df.empty:
        st.warning("No records currently available in the database.")
        return

    # Filter Controls
    with st.expander("🛠️ Advanced Search & Filter Options", expanded=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            all_plastics = sorted(df["plastic_abbreviation"].unique())
            selected_plastics = st.multiselect(
                "Filter by Plastic Type",
                options=all_plastics,
                default=all_plastics
            )
        with f_col2:
            all_qualities = ["HIGH", "MODERATE", "LOW", "UNVERIFIED"]
            selected_qualities = st.multiselect(
                "Filter by Evidence Quality",
                options=all_qualities,
                default=all_qualities
            )
        with f_col3:
            all_standards = sorted(df["standard_name"].unique())
            selected_standards = st.multiselect(
                "Filter by Standard Framework",
                options=all_standards,
                default=all_standards
            )

        f_col4, f_col5 = st.columns([2, 1])
        with f_col4:
            search_query = st.text_input(
                "🔎 Text Search (Microorganism, Strain, Enzyme, or Citation)",
                placeholder="e.g. Ideonella, cutinase, PAO1, 2016..."
            )
        with f_col5:
            all_sources = sorted(df["data_source"].unique())
            selected_sources = st.multiselect(
                "Data Source Type",
                options=all_sources,
                default=all_sources
            )

    # Apply Filters
    filtered_df = filter_trials_dataframe(
        df,
        plastics=selected_plastics,
        evidence_qualities=selected_qualities,
        standards=selected_standards,
        data_sources=selected_sources,
        search_query=search_query
    )

    st.markdown(
        f"**Showing {len(filtered_df)} of {len(df)} experimental trials matching filter criteria.**"
    )

    # Evidence Quality Legend
    display_evidence_legend()

    if filtered_df.empty:
        st.info("No experimental trials match your selected filter criteria.")
        return

    # Compact display table
    display_cols = [
        "trial_id",
        "plastic_abbreviation",
        "organism_name",
        "strain_id",
        "temperature",
        "pH",
        "incubation_duration_days",
        "weight_loss_percentage",
        "percentage_per_day",
        "analytical_confirmation",
        "evidence_quality",
        "standard_name",
        "data_source"
    ]
    
    st.dataframe(
        filtered_df[display_cols].rename(columns={
            "trial_id": "ID",
            "plastic_abbreviation": "Plastic",
            "organism_name": "Microorganism",
            "strain_id": "Strain",
            "temperature": "Temp (°C)",
            "pH": "pH",
            "incubation_duration_days": "Duration (d)",
            "weight_loss_percentage": "Weight Loss (%)",
            "percentage_per_day": "Rate (%/day)",
            "analytical_confirmation": "Analytical Method",
            "evidence_quality": "Evidence Tier",
            "standard_name": "Standard",
            "data_source": "Data Source"
        }),
        use_container_width=True,
        hide_index=True
    )

    # Detailed Inspection Expander
    st.markdown("---")
    st.markdown("### 📋 Detailed Trial Inspection")

    selected_trial_id = st.selectbox(
        "Select Trial ID to Inspect Complete Record:",
        options=filtered_df["trial_id"].tolist(),
        format_func=lambda tid: f"Trial #{tid}: {filtered_df[filtered_df['trial_id']==tid].iloc[0]['plastic_abbreviation']} – {filtered_df[filtered_df['trial_id']==tid].iloc[0]['organism_name']}"
    )

    if selected_trial_id:
        record = filtered_df[filtered_df["trial_id"] == selected_trial_id].iloc[0]

        card1, card2 = st.columns(2)
        with card1:
            st.markdown(f"#### 🧬 Polymer & Organism Profile (Trial #{record['trial_id']})")
            st.markdown(f"**Polymer:** {record['plastic_name']} (`{record['plastic_abbreviation']}`)")
            st.markdown(f"**Polymer Category:** {record['polymer_category']}")
            st.markdown(f"**Biological Agent:** *{record['organism_name']}* ({record['organism_type']})")
            st.markdown(f"**Strain Identifier:** `{record['strain_id']}`")
            st.markdown(f"**Culture Source:** {record['source_or_culture_collection'] or 'N/A'}")
            st.markdown(f"**Enzyme / Pathway:** {record['enzyme_information'] or 'N/A'}")

        with card2:
            st.markdown("#### 🌡️ Experimental Conditions")
            st.markdown(f"**Temperature:** {record['temperature']} °C | **pH:** {record['pH']}")
            st.markdown(f"**Incubation Duration:** {record['incubation_duration_days']} days")
            st.markdown(f"**Pretreatment:** {record['pretreatment_method']}")
            st.markdown(f"**Incubation System:** {record['incubation_method']}")
            st.markdown(f"**Medium Used:** {record['medium_used']}")
            st.markdown(f"**Geometric Surface Area:** {record['surface_area_cm2']} cm²" if pd.notna(record['surface_area_cm2']) else "**Surface Area:** Not reported")

        st.markdown("#### 📊 Quantitative Degradation & Evidence Quality")
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.metric("Weight Loss (%)", f"{record['weight_loss_percentage']:.2f}%")
        with r2:
            st.metric("Normalized Rate (%/day)", f"{record['percentage_per_day']:.4f}")
        with r3:
            s_rate = record['percentage_per_day_per_cm2']
            st.metric("Surface Rate (%/d/cm²)", f"{s_rate:.5f}" if pd.notna(s_rate) else "N/A")
        with r4:
            st.markdown("**Evidence Tier:**")
            st.markdown(render_evidence_badge(record['evidence_quality']), unsafe_allow_html=True)

        st.markdown(f"**Analytical Confirmation Technique:** `{record['analytical_confirmation']}`")
        st.markdown(f"**Reported Testing Standard:** `{record['standard_name']}` ({record['standard_number']}) | Formally Followed: **{record['standard_followed']}**")
        st.markdown(f"**Scientific Publication:** {record['publication_reference']}")
        if record.get("additional_observations"):
            st.info(f"**Additional Observations:** {record['additional_observations']}")

        # Delete Action
        with st.expander("🗑️ Admin Action: Delete this Trial Record"):
            st.warning("Deleting this trial will permanently remove the record from all database tables.")
            if st.button(f"Confirm Permanent Deletion of Trial #{selected_trial_id}", key=f"del_{selected_trial_id}"):
                success, msg = db_manager.delete_trial(selected_trial_id)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
