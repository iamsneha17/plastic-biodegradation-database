"""
Comparative Analysis Module for Streamlit UI.

Visualizes cross-polymer performance, microbial rankings, incubation kinetics,
pretreatment influences, and rate comparisons with scientific contextual disclaimers.
"""

import streamlit as st
import pandas as pd
from database import db_manager
from data_analysis import (
    filter_trials_dataframe,
    plot_degradation_by_plastic,
    plot_top_microorganisms,
    plot_duration_vs_weight_loss,
    plot_pretreatment_impact,
    plot_degradation_rates,
    plot_evidence_quality_distribution,
    plot_standards_distribution
)


def render_comparative_analysis_page():
    """Render the Comparative Analysis dashboard."""
    st.markdown("## 📊 Comparative Biodegradation Analysis")
    st.markdown(
        "Interactive graphical comparisons of microbial degradation efficiencies across "
        "polymer chemistries, biological strains, and environmental conditions."
    )

    # Scientific Caution Alert
    st.warning(
        r"""
        ⚖️ **Methodological Comparison Caveat:** 
        Degradation kinetics in published literature are governed by non-standardized parameters 
        including initial polymer molecular weight ($M_n$), degree of crystallinity ($\chi_c$), 
        film thickness, media composition, and agitation speed. 
        **Normalized rates should be compared in context with the underlying experimental setups.**
        """
    )

    df = db_manager.get_all_trials_df()
    if df.empty:
        st.info("No data available for comparative analysis.")
        return

    # Scope Filter
    with st.expander("🎯 Filter Analysis Scope", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            all_plastics = sorted(df["plastic_abbreviation"].unique())
            sel_plastics = st.multiselect("Substrates", options=all_plastics, default=all_plastics)
        with c2:
            all_eq = ["HIGH", "MODERATE", "LOW", "UNVERIFIED"]
            sel_eq = st.multiselect("Evidence Tiers", options=all_eq, default=all_eq)
        with c3:
            all_src = sorted(df["data_source"].unique())
            sel_src = st.multiselect("Data Source", options=all_src, default=all_src)

    filtered_df = filter_trials_dataframe(
        df,
        plastics=sel_plastics,
        evidence_qualities=sel_eq,
        data_sources=sel_src
    )

    if filtered_df.empty:
        st.warning("No records match the current analysis filter.")
        return

    # Tabs for distinct comparative angles
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔬 Polymer Degradability",
        "🧫 Microbial Performance",
        "⏱️ Kinetics & Pretreatment",
        "🛡️ Quality & Standards"
    ])

    with tab1:
        st.markdown("### Polymer Biodegradability Distribution")
        st.markdown(
            "Evaluation of gravimetric weight loss (%) across the six target plastic categories. "
            "Bio-based aliphatic polyesters (PHA and PLA) demonstrate significantly faster enzymatic cleavage "
            "compared to polyolefins (PE, PP) and aromatic synthetic polyesters (PET, PS)."
        )
        st.plotly_chart(plot_degradation_by_plastic(filtered_df), use_container_width=True)

        st.markdown("### Daily Normalized Degradation Rate (%/day)")
        st.plotly_chart(plot_degradation_rates(filtered_df), use_container_width=True)

    with tab2:
        st.markdown("### Top Performing Biological Agents")
        st.markdown(
            "Ranking of bacterial strains, fungal cultures, and microbial consortia by observed "
            "polymer degradation capability."
        )
        top_n = st.slider("Select number of organisms to display:", min_value=5, max_value=20, value=10)
        st.plotly_chart(plot_top_microorganisms(filtered_df, top_n=top_n), use_container_width=True)

    with tab3:
        st.markdown("### Incubation Kinetics (Duration vs. Weight Loss)")
        st.plotly_chart(plot_duration_vs_weight_loss(filtered_df), use_container_width=True)

        st.markdown("### Pretreatment Method Efficacy")
        st.markdown(
            "Recalcitrant polyolefins (PE, PP) typically require prior abiotic photo-oxidation (UV) "
            "or thermal aging to introduce hydrophilic carbonyl groups ($C=O$) necessary for microbial enzyme recognition."
        )
        st.plotly_chart(plot_pretreatment_impact(filtered_df), use_container_width=True)

    with tab4:
        st.markdown("### Analytical Evidence & Testing Standards")
        q_col1, q_col2 = st.columns(2)
        with q_col1:
            st.plotly_chart(plot_evidence_quality_distribution(filtered_df), use_container_width=True)
        with q_col2:
            st.plotly_chart(plot_standards_distribution(filtered_df), use_container_width=True)
