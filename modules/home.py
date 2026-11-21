"""
Home Dashboard Module for Streamlit UI.

Presents high-level metrics, system architecture status, evidence-quality breakdown,
and comprehensive biotechnology overview.
"""

import streamlit as st
import pandas as pd
from database import db_manager
from data_analysis import (
    get_database_kpis,
    plot_evidence_quality_distribution,
    plot_degradation_by_plastic
)
from modules.evidence_quality import display_evidence_legend
from config import TARGET_PLASTICS


def render_home_page():
    """Render the Home Dashboard page."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                    color: white; padding: 22px 28px; border-radius: 12px; margin-bottom: 25px;">
            <h1 style="margin: 0; font-size: 2.1rem; color: white;">
                🧬 Plastic Biodegradation Trial Database & Analysis System
            </h1>
            <p style="margin-top: 8px; margin-bottom: 0; font-size: 1.05rem; opacity: 0.92;">
                A centralized academic database for collecting, managing, and quantitatively comparing 
                published microbial biodegradation trials across synthetic and bio-based plastics.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 1. Database Connection Status Banner
    status = db_manager.get_status()
    if "MySQL" in status["engine_type"]:
        st.success(
            f"✅ **Database Connected:** {status['engine_type']} on `{status['host']}` "
            f"| Schema: `{status['database_name']}`"
        )
    else:
        st.info(
            f"ℹ️ **Database Mode:** {status['engine_type']} | Storage: `{status['database_name']}`\n\n"
            f"{status['error_message'] or ''}\n\n"
            "💡 *Tip:* To switch to a dedicated MySQL server, update credentials in your `.env` file and "
            "import `database/schema.sql` into your MySQL instance."
        )

    # 2. Fetch Data
    df = db_manager.get_all_trials_df()
    kpis = get_database_kpis(df)

    # 3. KPI Metric Cards
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric(label="Total Trials", value=kpis["total_trials"])
    with m2:
        st.metric(label="Plastic Types", value=f"{kpis['total_plastics']} / 6")
    with m3:
        st.metric(label="Microorganisms", value=kpis["total_organisms"])
    with m4:
        st.metric(label="ASTM/ISO Trials", value=kpis["total_standards_followed"])
    with m5:
        st.metric(label="High Evidence", value=f"{kpis['high_evidence_count']} ({kpis['high_evidence_count']/max(kpis['total_trials'], 1)*100:.0f}%)")

    st.markdown("---")

    # 4. Interactive Summary Visualizations
    col1, col2 = st.columns([1.1, 1.4])
    with col1:
        st.plotly_chart(plot_evidence_quality_distribution(df), use_container_width=True)
    with col2:
        st.plotly_chart(plot_degradation_by_plastic(df), use_container_width=True)

    # 5. Evidence Quality Legend
    display_evidence_legend()

    # 6. Target Plastics Reference Cards
    st.markdown("### 🔬 Target Polymer Catalog")
    st.markdown(
        "The system evaluates microbial depolymerization kinetics across six primary target plastics:"
    )

    p_cols = st.columns(3)
    for idx, plastic in enumerate(TARGET_PLASTICS):
        with p_cols[idx % 3]:
            # Count in DB
            count = len(df[df["plastic_abbreviation"] == plastic["abbreviation"]]) if not df.empty else 0
            st.markdown(
                f"""
                <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 14px; 
                            margin-bottom: 15px; background-color: #fafbfc; height: 100%;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <h4 style="margin: 0; color: #1e3c72;">{plastic['abbreviation']}</h4>
                        <span style="font-size: 0.8rem; background: #e8f0fe; color: #1967d2; 
                                     padding: 2px 8px; border-radius: 10px; font-weight: bold;">
                            {count} Trials
                        </span>
                    </div>
                    <div style="font-size: 0.85rem; font-weight: 600; color: #495057; margin-top: 4px;">
                        {plastic['name']}
                    </div>
                    <div style="font-size: 0.78rem; color: #6c757d; margin-bottom: 8px;">
                        Category: <em>{plastic['category']}</em>
                    </div>
                    <p style="font-size: 0.82rem; color: #333; margin: 0; line-height: 1.4;">
                        {plastic['description']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # 7. Biotechnology Context & Degradation Mechanism
    st.markdown("### 🧫 Biological Plastic Depolymerization Mechanism")
    st.markdown(
        """
        Microbial degradation of recalcitrant synthetic and bio-based plastics progresses through four distinct stages:

        1. **Bio-deterioration & Surface Attachment:** Microorganisms adhere to the hydrophobic polymer substrate, 
           forming dense biofilms mediated by extracellular polymeric substances (EPS) and biosurfactants.
        2. **Bio-fragmentation (Enzymatic Depolymerization):** Secreted microbial enzymes (e.g. cutinases, PETases, 
           esterases, lipases, and monooxygenases) hydrolyze high-molecular-weight polymer backbones into water-soluble 
           oligomers, dimers, and monomers.
        3. **Bio-assimilation:** Microbial cells uptake the cleaved low-molecular-weight degradation products across the 
           cell membrane into primary metabolic pathways.
        4. **Mineralization:** Assimilated carbon is completely metabolized via the TCA cycle into carbon dioxide 
           ($\\text{CO}_2$), water ($\\text{H}_2\\text{O}$), and new microbial biomass under aerobic conditions, or methane 
           ($\\text{CH}_4$) under anaerobic conditions.
        """
    )
