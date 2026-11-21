"""
====================================================================
Plastic Biodegradation Trial Database and Analysis System
Main Application Entry Point (Streamlit)
====================================================================
"""

import os
import streamlit as st

# Configure page settings
st.set_page_config(
    page_title="Plastic Biodegradation Trial Database",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Biotechnology CSS styling
st.markdown(
    """
    <style>
        /* Base typography and clean layout */
        .main {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        
        /* Metric Card Enhancements */
        div[data-testid="stMetric"] {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.82rem;
            font-weight: 600;
            color: #495057;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.6rem;
            font-weight: 700;
            color: #1e3c72;
        }
        
        /* Custom quality badge tags */
        .badge-high {
            background-color: #d4edda;
            color: #155724;
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        .badge-mod {
            background-color: #d1ecf1;
            color: #0c5460;
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        .badge-low {
            background-color: #fff3cd;
            color: #856404;
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #f8fafc;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize database schema and default sample data
from database import init_system_database, db_manager

try:
    init_system_database()
except Exception as e:
    st.error(f"Error during database initialization: {e}")

# Import UI Modules
from modules.home import render_home_page
from modules.add_trial import render_add_trial_page
from modules.browse_trials import render_browse_trials_page
from modules.comparative_analysis import render_comparative_analysis_page
from modules.research_sources import render_research_sources_page
from modules.reports import render_reports_page

# Sidebar Navigation
st.sidebar.markdown(
    """
    <div style="text-align: center; padding: 10px 0 15px 0;">
        <h2 style="margin: 0; color: #1e3c72; font-size: 1.4rem;">🧬 PlastiDeg DB</h2>
        <span style="font-size: 0.82rem; color: #6c757d; font-weight: 500;">
            Plastic Biodegradation Trial System
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

menu_options = [
    "🏠 Home Dashboard",
    "➕ Add Experimental Trial",
    "🔍 Browse Database",
    "📊 Comparative Analysis",
    "📚 Research Sources & Standards",
    "📑 Reports & Export"
]

choice = st.sidebar.radio("Navigation Menu", options=menu_options)

# Sidebar System Metadata
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗄️ System Architecture")
status = db_manager.get_status()

if "MySQL" in status["engine_type"]:
    st.sidebar.success(f"🟢 **Database:** {status['engine_type']}\n\n**Host:** `{status['host']}`")
else:
    st.sidebar.info(f"🟡 **Database:** {status['engine_type']}\n\n**Host:** `{status['host']}`")

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="font-size: 0.78rem; color: #6c757d; line-height: 1.4;">
        <strong>Target Polymers:</strong><br>
        PET • PE • PP • PS • PLA • PHA<br><br>
        <strong>Academic Project:</strong><br>
        Biotechnology + Python + MySQL Relational Database System.
    </div>
    """,
    unsafe_allow_html=True
)

# Route to selected page
if choice == "🏠 Home Dashboard":
    render_home_page()
elif choice == "➕ Add Experimental Trial":
    render_add_trial_page()
elif choice == "🔍 Browse Database":
    render_browse_trials_page()
elif choice == "📊 Comparative Analysis":
    render_comparative_analysis_page()
elif choice == "📚 Research Sources & Standards":
    render_research_sources_page()
elif choice == "📑 Reports & Export":
    render_reports_page()
