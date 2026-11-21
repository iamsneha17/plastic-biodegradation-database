"""
Evidence Quality Helper and UI Component.

Renders colored badges and explains the 4-tier scientific analytical classification.
"""

import streamlit as st
from config import EVIDENCE_LEVELS


def render_evidence_badge(quality: str) -> str:
    """Return an HTML snippet for a colored pill badge."""
    q = str(quality).upper().strip()
    config = EVIDENCE_LEVELS.get(q, EVIDENCE_LEVELS["UNVERIFIED"])
    color = config["color"]
    bg_color = config["bg_color"]

    return (
        f'<span style="background-color: {bg_color}; color: {color}; '
        f'padding: 3px 10px; border-radius: 12px; font-weight: 600; '
        f'font-size: 0.82rem; border: 1px solid {color}40; display: inline-block;">'
        f'{q}</span>'
    )


def display_evidence_legend():
    """Display an informative callout box explaining evidence quality levels."""
    with st.expander("ℹ️ Scientific Evidence Quality Classification Guide", expanded=False):
        st.markdown(
            """
            Scientific literature on plastic biodegradation varies substantially in analytical rigor. 
            To assist researchers in distinguishing definitive enzymatic depolymerization from superficial biofilm attachment, 
            trials in this database are stratified into four analytical tiers:

            | Tier | Analytical Confirmation Criteria | Examples |
            | :--- | :--- | :--- |
            | <span style="color:#28a745; font-weight:bold;">HIGH</span> | **Multiple orthogonal techniques** directly verifying polymer chain scission, molecular weight shifts, or monomer liberation. | FTIR + SEM, FTIR + GPC, <sup>13</sup>C-CO<sub>2</sub> Respirometry + HPLC |
            | <span style="color:#17a2b8; font-weight:bold;">MODERATE</span> | **Single analytical method** demonstrating surface erosion, chemical modification, or molecular weight reduction. | FTIR alone, SEM alone, or GPC alone |
            | <span style="color:#fd7e14; font-weight:bold;">LOW</span> | **Gravimetric weight loss or visual clearance alone** without chemical or structural confirmation. | Dry mass change only, agar clearing zones |
            | <span style="color:#6c757d; font-weight:bold;">UNVERIFIED</span> | **Preliminary, non-peer-reviewed, or unverified** literature sources. | Non-refereed tech reports, exploratory screenings |

            > **Important Distinction:** Analytical evidence quality is **strictly decoupled** from formal compliance with ASTM/ISO standards. 
            > A study may possess HIGH analytical evidence (e.g. Science or Nature publications utilizing advanced synchrotron X-ray or NMR) 
            > without adhering to industrial ASTM D5338 composting protocols, and vice versa.
            """,
            unsafe_allow_html=True
        )
