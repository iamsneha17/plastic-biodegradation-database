"""
Research Sources & Scientific Standards Module for Streamlit UI.

Provides full bibliographic citations, DOI hyperlinks, integration references for
the PAZy (Plastic Active Enzymes Database), microbial culture collections,
and standard definitions for ASTM and ISO testing frameworks.
"""

import streamlit as st
import pandas as pd
from database import db_manager


def render_research_sources_page():
    """Render the Research Sources & Standards Reference page."""
    st.markdown("## 📚 Scientific Literature Sources & Reference Standards")
    st.markdown(
        "Complete traceability for all published peer-reviewed studies integrated into the database, "
        "along with official metadata for testing standards and biotechnology resource repositories."
    )

    df = db_manager.get_all_trials_df()

    # Tabs for Sources vs Standards vs External Repositories
    tab1, tab2, tab3 = st.tabs([
        "📖 Literature Bibliography",
        "📐 ASTM & ISO Standards Catalog",
        "🌐 External Biotechnology Databases"
    ])

    with tab1:
        st.markdown("### Published Research Papers")
        st.markdown(
            "Every scientific record in this database is traced back to its published peer-reviewed "
            "source or explicitly marked as an illustrative educational demo."
        )

        if not df.empty:
            # Group by publication reference to avoid duplicate citation displays
            papers = (
                df.groupby("publication_reference")
                .agg({
                    "publication_year": "first",
                    "data_source": "first",
                    "plastic_abbreviation": lambda x: ", ".join(sorted(set(x))),
                    "organism_name": lambda x: ", ".join(sorted(set(x))),
                    "evidence_quality": "first",
                    "trial_id": "count"
                })
                .reset_index()
                .rename(columns={"trial_id": "trials_recorded"})
                .sort_values(by="publication_year", ascending=False)
            )

            for _, paper in papers.iterrows():
                is_verified = paper["data_source"] == "Verified Literature"
                border_color = "#28a745" if is_verified else "#ffc107"
                badge_text = "Verified Literature" if is_verified else "Illustrative Demo"

                st.markdown(
                    f"""
                    <div style="border-left: 4px solid {border_color}; padding: 12px 18px; 
                                margin-bottom: 15px; background-color: #f8f9fa; border-radius: 0 8px 8px 0;">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <span style="font-weight: bold; font-size: 1.0rem; color: #1e3c72;">
                                {paper['publication_reference']}
                            </span>
                            <span style="font-size: 0.78rem; font-weight: 600; padding: 2px 8px; border-radius: 10px; 
                                         background-color: {'#e6f4ea' if is_verified else '#fef7e0'}; 
                                         color: {'#137333' if is_verified else '#b06000'};">
                                {badge_text}
                            </span>
                        </div>
                        <div style="margin-top: 6px; font-size: 0.85rem; color: #495057;">
                            <strong>Year:</strong> {paper['publication_year'] or 'N/A'} | 
                            <strong>Target Polymers:</strong> <code>{paper['plastic_abbreviation']}</code> | 
                            <strong>Organisms Evaluated:</strong> <em>{paper['organism_name']}</em> | 
                            <strong>Trials Derived:</strong> {paper['trials_recorded']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with tab2:
        st.markdown("### International Biodegradation Testing Standards")
        st.markdown(
            """
            > ⚠️ **Scientific Distinction:** The specifications below represent standardized testing definitions. 
            > A study is only categorized as complying with a standard if the author explicitly adhered to the protocol 
            > in the published manuscript.
            """
        )

        standards_info = [
            {
                "framework": "ISO 14855-1 / 14855-2",
                "title": "Determination of the ultimate aerobic biodegradability of plastic materials under controlled composting conditions",
                "description": "Measures mineralization by quantifying evolved carbon dioxide using respirometric gas chromatography or infrared gas analysis under thermophilic (58°C) composting conditions.",
                "applicability": "Compostable polymers such as PLA and PHA."
            },
            {
                "framework": "ASTM D5338",
                "title": "Standard Test Method for Determining Aerobic Biodegradation of Plastic Materials Under Controlled Composting Conditions",
                "description": "American counterpart to ISO 14855. Evaluates the percentage of organic carbon converted to CO2 in a controlled municipal solid waste compost matrix.",
                "applicability": "Compostable biopolyesters (PLA, PHA)."
            },
            {
                "framework": "ISO 17556",
                "title": "Determination of the ultimate aerobic biodegradability of plastic materials in soil by measuring the oxygen demand in a respirometer or the amount of carbon dioxide evolved",
                "description": "Standardized soil respirometry measuring O2 consumption or CO2 production in natural soil microcosms over 6 to 24 months.",
                "applicability": "Soil-biodegradable polymers and agricultural mulch films (PHA, pretreated PE)."
            },
            {
                "framework": "ASTM D5988",
                "title": "Standard Test Method for Determining Aerobic Biodegradation of Plastic Materials in Soil",
                "description": "Soil burial test measuring CO2 absorption in alkaline traps (Ba(OH)2 or NaOH) with acid titration to calculate biodegradation percentage.",
                "applicability": "Agricultural and packaging plastics exposed to terrestrial environments."
            },
            {
                "framework": "ASTM D5210",
                "title": "Standard Test Method for Determining the Anaerobic Biodegradation of Plastic Materials in the Presence of Municipal Sewage Sludge",
                "description": "Assesses anaerobic digestion kinetics by measuring biogas (CH4 + CO2) production in anaerobic digester sludge.",
                "applicability": "Anaerobic digester and marine sediment evaluation."
            }
        ]

        for std in standards_info:
            with st.expander(f"📌 {std['framework']} – {std['title']}"):
                st.markdown(f"**Scope & Methodology:** {std['description']}")
                st.markdown(f"**Typical Applicability:** {std['applicability']}")

    with tab3:
        st.markdown("### External Biological Data Repositories & Databases")
        st.markdown(
            "The following public bioinformatics resources can be cross-referenced for enzyme sequences and culture strains:"
        )

        ext_col1, ext_col2 = st.columns(2)
        with ext_col1:
            st.markdown(
                """
                #### 🧬 PAZy – Plastics-Active Enzymes Database
                - **Focus:** Curated repository of verified plastic-depolymerizing enzymes (cutinases, PETases, esterases, laccases, and alkane hydroxylases).
                - **Access:** [pazy.eu](https://pazy.eu/)
                - **Content:** Sequence alignments, catalytic residues, substrate specificities, and kinetic parameters ($k_{cat}$, $K_m$).
                
                #### 🧫 ATCC – American Type Culture Collection
                - **Focus:** Global biological resource center providing authenticated microbial strains (e.g. *Pseudomonas aeruginosa* ATCC 15692, *Amycolatopsis orientalis* ATCC 43491).
                - **Access:** [atcc.org](https://www.atcc.org/)
                """
            )
        with ext_col2:
            st.markdown(
                """
                #### 🔬 DSMZ – German Collection of Microorganisms and Cell Cultures
                - **Focus:** Renowned European culture collection holding plastic-degrading reference strains (e.g. *Thermobifida fusca* DSM 43793, *Cupriavidus necator* DSM 428).
                - **Access:** [dsmz.de](https://www.dsmz.de/)
                
                #### 📚 NCBI – National Center for Biotechnology Information
                - **Focus:** GeneBank repository for 16S rRNA identification sequences, metagenomic assemblies of plastic-eating microbiomes, and enzyme protein structures.
                - **Access:** [ncbi.nlm.nih.gov](https://www.ncbi.nlm.nih.gov/)
                """
            )
