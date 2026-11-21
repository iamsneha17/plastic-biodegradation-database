"""
Modules Package for Plastic Biodegradation Trial Database and Analysis System.

Exposes page rendering components and UI helper utilities for Streamlit.
"""

from modules.home import render_home_page
from modules.add_trial import render_add_trial_page
from modules.browse_trials import render_browse_trials_page
from modules.comparative_analysis import render_comparative_analysis_page
from modules.research_sources import render_research_sources_page
from modules.reports import render_reports_page
from modules.evidence_quality import render_evidence_badge, display_evidence_legend

__all__ = [
    "render_home_page",
    "render_add_trial_page",
    "render_browse_trials_page",
    "render_comparative_analysis_page",
    "render_research_sources_page",
    "render_reports_page",
    "render_evidence_badge",
    "display_evidence_legend",
]
