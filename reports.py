"""
Reports and Data Export Module for Streamlit UI.

Provides:
- CSV export
- Styled Microsoft Excel (.xlsx) export
- Multi-page Academic PDF Summary Report generated via Matplotlib's vector PdfPages backend
"""

import io
import os
import datetime
from typing import Optional
import streamlit as st
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from database import db_manager
from data_analysis import filter_trials_dataframe, get_database_kpis
from config import REPORTS_DIR

import tempfile

# Set writable Matplotlib config directory for cloud & container environments
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))

# Ensure matplotlib uses a non-interactive backend
matplotlib.use("Agg")


def generate_pdf_report(df: pd.DataFrame, title: str = "Plastic Biodegradation Trial Analysis Report") -> bytes:
    """
    Generate an academic multi-page PDF summary report using Matplotlib's PdfPages.
    Returns bytes of the PDF file.
    """
    buffer = io.BytesIO()
    
    with PdfPages(buffer) as pdf:
        # ----------------------------------------------------
        # Page 1: Executive Summary & Overview
        # ----------------------------------------------------
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis("off")

        # Header Title
        fig.text(0.5, 0.93, "PLASTIC BIODEGRADATION TRIAL DATABASE", 
                 ha="center", va="center", fontsize=16, fontweight="bold", color="#1e3c72")
        fig.text(0.5, 0.90, "Scientific Experimental Trial Summary & Comparative Analysis Report", 
                 ha="center", va="center", fontsize=11, fontstyle="italic", color="#495057")
        fig.text(0.5, 0.875, f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Target Polymers: PET, PE, PP, PS, PLA, PHA",
                 ha="center", va="center", fontsize=8.5, color="#6c757d")

        # Horizontal Divider
        line = plt.Line2D([0.08, 0.92], [0.86, 0.86], color="#1e3c72", linewidth=1.5, transform=fig.transFigure)
        fig.add_artist(line)

        # Summary KPIs
        kpis = get_database_kpis(df)
        kpi_text = (
            f"• Total Experimental Trials Included: {kpis['total_trials']}\n"
            f"• Plastic Polymer Substrates Evaluated: {kpis['total_plastics']} types\n"
            f"• Microorganisms & Microbial Consortia: {kpis['total_organisms']} distinct biological agents\n"
            f"• Trials Adhering to ASTM/ISO Testing Protocols: {kpis['total_standards_followed']}\n"
            f"• High Analytical Evidence Tier Trials: {kpis['high_evidence_count']} "
            f"({kpis['high_evidence_count']/max(kpis['total_trials'], 1)*100:.1f}%)\n"
            f"• Mean Observed Gravimetric Weight Loss: {kpis['avg_weight_loss']}%\n"
            f"• Mean Incubation Period: {kpis['avg_duration']} days"
        )
        fig.text(0.1, 0.77, "1. EXECUTIVE SUMMARY & DATABASE METRICS", fontsize=11, fontweight="bold", color="#1e3c72")
        fig.text(0.12, 0.64, kpi_text, fontsize=9.5, linespacing=1.6, color="#212529")

        # Mini Bar Chart on Page 1: Average Weight Loss by Plastic Type
        chart_ax = fig.add_axes([0.15, 0.28, 0.7, 0.28])
        if not df.empty:
            summary = df.groupby("plastic_abbreviation")["weight_loss_percentage"].mean().reindex(
                ["PET", "PE", "PP", "PS", "PLA", "PHA"]
            ).fillna(0.0)
            colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948"]
            bars = chart_ax.bar(summary.index, summary.values, color=colors, edgecolor="#333333", width=0.55)
            chart_ax.set_title("Mean Biodegradation Weight Loss (%) by Polymer Substrate", fontsize=10, fontweight="bold")
            chart_ax.set_ylabel("Weight Loss (%)", fontsize=9)
            chart_ax.set_ylim(0, max(summary.values.max() * 1.15, 10))
            chart_ax.grid(axis="y", linestyle="--", alpha=0.5)
            for bar in bars:
                height = bar.get_height()
                chart_ax.annotate(f"{height:.1f}%",
                                  xy=(bar.get_x() + bar.get_width() / 2, height),
                                  xytext=(0, 3), textcoords="offset points",
                                  ha="center", va="bottom", fontsize=8, fontweight="bold")

        # Methodological Disclaimer
        notice_text = (
            "METHODOLOGICAL NOTE: Biodegradation kinetics depend critically on experimental geometry, polymer\n"
            "crystallinity, surface area, and culture conditions. Normalized degradation rates (%/day) provide\n"
            "comparative screening indicators rather than universal kinetic constants."
        )
        fig.text(0.1, 0.15, notice_text, fontsize=8, fontstyle="italic", color="#6c757d",
                 bbox=dict(boxstyle="square,pad=0.6", facecolor="#f8f9fa", edgecolor="#ced4da"))

        fig.text(0.5, 0.05, "Page 1 of 2 – Plastic Biodegradation Trial Database & Analysis System",
                 ha="center", fontsize=8, color="#868e96")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        # ----------------------------------------------------
        # Page 2: Tabular Summary of Experimental Trials
        # ----------------------------------------------------
        fig2, ax2 = plt.subplots(figsize=(8.5, 11))
        ax2.axis("off")

        fig2.text(0.5, 0.94, "EXPERIMENTAL TRIAL REGISTRY", ha="center", fontsize=14, fontweight="bold", color="#1e3c72")
        fig2.text(0.5, 0.915, "Individual Microbial Biodegradation Trial Records & Analytical Evidence Tiers",
                  ha="center", fontsize=9.5, fontstyle="italic", color="#495057")

        line2 = plt.Line2D([0.08, 0.92], [0.895, 0.895], color="#1e3c72", linewidth=1.5, transform=fig2.transFigure)
        fig2.add_artist(line2)

        # Prepare Table Data (Top 18 records to fit page neatly)
        sample_df = df.head(18)
        table_data = [
            ["ID", "Plastic", "Microorganism / Biological Agent", "Temp", "pH", "Days", "Loss %", "Rate (%/d)", "Evidence", "Standard"]
        ]
        for _, row in sample_df.iterrows():
            org_short = str(row["organism_name"])[:24]
            table_data.append([
                str(row["trial_id"]),
                str(row["plastic_abbreviation"]),
                org_short,
                f"{row['temperature']}°C",
                f"{row['pH']}",
                f"{row['incubation_duration_days']}",
                f"{row['weight_loss_percentage']:.1f}%",
                f"{row['percentage_per_day']:.3f}",
                str(row["evidence_quality"]),
                str(row["standard_name"])
            ])

        tab_ax = fig2.add_axes([0.05, 0.12, 0.9, 0.74])
        tab_ax.axis("off")
        pdf_table = tab_ax.table(
            cellText=table_data,
            loc="center",
            cellLoc="center",
            colWidths=[0.06, 0.09, 0.32, 0.08, 0.06, 0.08, 0.09, 0.11, 0.11, 0.10]
        )
        pdf_table.auto_set_font_size(False)
        pdf_table.set_fontsize(7.5)
        pdf_table.scale(1, 1.35)

        # Style Header Row
        for (i, j), cell in pdf_table.get_celld().items():
            if i == 0:
                cell.set_facecolor("#1e3c72")
                cell.set_text_props(color="white", fontweight="bold")
            elif i % 2 == 1:
                cell.set_facecolor("#f1f3f5")
            else:
                cell.set_facecolor("#ffffff")

        fig2.text(0.5, 0.05, "Page 2 of 2 – Plastic Biodegradation Trial Database & Analysis System",
                  ha="center", fontsize=8, color="#868e96")
        pdf.savefig(fig2, bbox_inches="tight")
        plt.close(fig2)

    buffer.seek(0)
    return buffer.getvalue()


def render_reports_page():
    """Render the Reports & Data Export dashboard page."""
    st.markdown("## 📑 Data Export & Scientific Reports")
    st.markdown(
        "Generate publication-ready summary reports and export filtered experimental trial datasets "
        "in CSV, Microsoft Excel (.xlsx), and multi-page vector PDF formats."
    )

    df = db_manager.get_all_trials_df()
    if df.empty:
        st.warning("No records available to export.")
        return

    # Filter selector for export
    with st.expander("🎯 Select Export Data Scope", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            all_plastics = sorted(df["plastic_abbreviation"].unique())
            sel_plastics = st.multiselect("Plastic Types", options=all_plastics, default=all_plastics, key="rep_p")
        with c2:
            all_eq = ["HIGH", "MODERATE", "LOW", "UNVERIFIED"]
            sel_eq = st.multiselect("Evidence Tiers", options=all_eq, default=all_eq, key="rep_eq")
        with c3:
            all_src = sorted(df["data_source"].unique())
            sel_src = st.multiselect("Data Sources", options=all_src, default=all_src, key="rep_src")

    export_df = filter_trials_dataframe(
        df,
        plastics=sel_plastics,
        evidence_qualities=sel_eq,
        data_sources=sel_src
    )

    st.info(f"Target dataset contains **{len(export_df)}** experimental trial records.")

    # Export Buttons
    col1, col2, col3 = st.columns(3)

    # 1. CSV Export
    with col1:
        st.markdown("#### 📄 CSV Export")
        st.markdown("Raw tabular data with comma delimiters, compatible with R, Python, and SPSS.")
        csv_bytes = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download CSV Dataset",
            data=csv_bytes,
            file_name=f"plastic_biodegradation_trials_{datetime.date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # 2. Excel Export
    with col2:
        st.markdown("#### 📊 Excel Export (.xlsx)")
        st.markdown("Formatted spreadsheet with separate summary and detailed trial sheets.")
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            export_df.to_excel(writer, sheet_name="Trial_Data", index=False)
            # Create a quick summary sheet
            summary_pivot = export_df.groupby("plastic_abbreviation").agg(
                Trials=("trial_id", "count"),
                Mean_Weight_Loss=("weight_loss_percentage", "mean"),
                Max_Weight_Loss=("weight_loss_percentage", "max"),
                Mean_Rate_per_day=("percentage_per_day", "mean")
            ).reset_index()
            summary_pivot.to_excel(writer, sheet_name="Polymer_Summary", index=False)
        excel_data = excel_buffer.getvalue()

        st.download_button(
            label="⬇️ Download Excel Workbook",
            data=excel_data,
            file_name=f"plastic_biodegradation_trials_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # 3. PDF Summary Report
    with col3:
        st.markdown("#### 📑 Academic PDF Report")
        st.markdown("Multi-page summary report with executive metrics, charts, and trial registry.")
        pdf_data = generate_pdf_report(export_df)
        st.download_button(
            label="⬇️ Download PDF Summary Report",
            data=pdf_data,
            file_name=f"plastic_biodegradation_summary_report_{datetime.date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # Preview of Export Data
    st.markdown("---")
    st.markdown("### 👁️ Dataset Preview")
    st.dataframe(export_df.head(10), use_container_width=True)
