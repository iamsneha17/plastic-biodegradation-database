"""
Data Analysis and Scientific Visualization Module.

Generates academic figures, interactive Plotly charts, and statistical summaries
for comparing microbial degradation performance across polymer substrates.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from config import EVIDENCE_LEVELS


def get_database_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate key performance indicators and summary metrics."""
    if df.empty:
        return {
            "total_trials": 0,
            "total_plastics": 0,
            "total_organisms": 0,
            "total_standards_followed": 0,
            "verified_literature_count": 0,
            "illustrative_demo_count": 0,
            "high_evidence_count": 0,
            "avg_weight_loss": 0.0,
            "avg_duration": 0.0
        }

    total_trials = len(df)
    total_plastics = df["plastic_abbreviation"].nunique()
    total_organisms = df["organism_name"].nunique()
    
    # Standards followed
    std_mask = (df["standard_followed"].astype(str).str.lower().isin(["yes", "true", "followed"])) | (
        df["standard_name"].astype(str).str.upper().isin(["ASTM", "ISO"])
    )
    total_standards = int(std_mask.sum())
    
    verified_count = int((df["data_source"] == "Verified Literature").sum())
    demo_count = int((df["data_source"] == "Illustrative Demo").sum())
    high_ev_count = int((df["evidence_quality"] == "HIGH").sum())
    avg_loss = float(df["weight_loss_percentage"].mean()) if "weight_loss_percentage" in df else 0.0
    avg_dur = float(df["incubation_duration_days"].mean()) if "incubation_duration_days" in df else 0.0

    return {
        "total_trials": total_trials,
        "total_plastics": total_plastics,
        "total_organisms": total_organisms,
        "total_standards_followed": total_standards,
        "verified_literature_count": verified_count,
        "illustrative_demo_count": demo_count,
        "high_evidence_count": high_ev_count,
        "avg_weight_loss": round(avg_loss, 2),
        "avg_duration": round(avg_dur, 1)
    }


def filter_trials_dataframe(
    df: pd.DataFrame,
    plastics: Optional[List[str]] = None,
    evidence_qualities: Optional[List[str]] = None,
    standards: Optional[List[str]] = None,
    organism_types: Optional[List[str]] = None,
    data_sources: Optional[List[str]] = None,
    search_query: Optional[str] = None
) -> pd.DataFrame:
    """Filter the master trials DataFrame according to user-selected sidebar criteria."""
    if df.empty:
        return df

    filtered = df.copy()

    if plastics:
        filtered = filtered[filtered["plastic_abbreviation"].isin(plastics)]

    if evidence_qualities:
        filtered = filtered[filtered["evidence_quality"].isin(evidence_qualities)]

    if standards:
        filtered = filtered[filtered["standard_name"].isin(standards)]

    if organism_types:
        filtered = filtered[filtered["organism_type"].isin(organism_types)]

    if data_sources:
        filtered = filtered[filtered["data_source"].isin(data_sources)]

    if search_query and search_query.strip():
        q = search_query.strip().lower()
        search_mask = (
            filtered["organism_name"].astype(str).str.lower().str.contains(q) |
            filtered["strain_id"].astype(str).str.lower().str.contains(q) |
            filtered["enzyme_information"].astype(str).str.lower().str.contains(q) |
            filtered["publication_reference"].astype(str).str.lower().str.contains(q)
        )
        filtered = filtered[search_mask]

    return filtered


# ====================================================================
# Plotly Scientific Visualizations
# ====================================================================

def plot_degradation_by_plastic(df: pd.DataFrame) -> go.Figure:
    """Box plot and jittered scatter points of degradation percentage across plastic substrates."""
    if df.empty:
        return go.Figure()

    fig = px.box(
        df,
        x="plastic_abbreviation",
        y="weight_loss_percentage",
        color="polymer_category",
        points="all",
        hover_data=["organism_name", "incubation_duration_days", "evidence_quality", "data_source"],
        labels={
            "plastic_abbreviation": "Plastic Polymer",
            "weight_loss_percentage": "Weight Loss (%)",
            "polymer_category": "Polymer Class"
        },
        title="<b>Polymer Biodegradability: Weight Loss Distribution by Plastic Type</b>",
        category_orders={"plastic_abbreviation": ["PET", "PE", "PP", "PS", "PLA", "PHA"]}
    )
    fig.update_layout(
        template="plotly_white",
        xaxis_title="<b>Plastic Polymer Type</b>",
        yaxis_title="<b>Observed Weight Loss (%)</b>",
        legend_title="Polymer Class",
        hoverlabel=dict(bgcolor="white", font_size=12),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


def plot_top_microorganisms(df: pd.DataFrame, top_n: int = 12) -> go.Figure:
    """Horizontal bar chart showing top microorganisms ranked by highest weight loss percentage."""
    if df.empty:
        return go.Figure()

    # Sort by weight loss
    ranked = df.sort_values("weight_loss_percentage", ascending=False).head(top_n)

    fig = px.bar(
        ranked,
        x="weight_loss_percentage",
        y="organism_name",
        orientation="h",
        color="plastic_abbreviation",
        hover_data=["strain_id", "incubation_duration_days", "percentage_per_day", "evidence_quality"],
        labels={
            "weight_loss_percentage": "Weight Loss (%)",
            "organism_name": "Microorganism / Consortium",
            "plastic_abbreviation": "Substrate"
        },
        title=f"<b>Top {top_n} Microbial Trials by Gravimetric Weight Loss</b>",
        category_orders={"plastic_abbreviation": ["PET", "PE", "PP", "PS", "PLA", "PHA"]}
    )
    fig.update_layout(
        template="plotly_white",
        yaxis=dict(autorange="reversed"),
        xaxis_title="<b>Weight Loss (%)</b>",
        yaxis_title="<b>Microorganism / Biological Agent</b>",
        hoverlabel=dict(bgcolor="white", font_size=12),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


def plot_duration_vs_weight_loss(df: pd.DataFrame) -> go.Figure:
    """Interactive scatter plot of Incubation Duration vs. Weight Loss (%)."""
    if df.empty:
        return go.Figure()

    # Bubble size based on temperature or duration
    fig = px.scatter(
        df,
        x="incubation_duration_days",
        y="weight_loss_percentage",
        color="plastic_abbreviation",
        symbol="organism_type",
        size="temperature",
        hover_data=[
            "organism_name", "temperature", "pH", 
            "pretreatment_method", "analytical_confirmation", "evidence_quality"
        ],
        labels={
            "incubation_duration_days": "Incubation Duration (Days)",
            "weight_loss_percentage": "Weight Loss (%)",
            "plastic_abbreviation": "Plastic",
            "temperature": "Temp (°C)"
        },
        title="<b>Incubation Duration vs. Biodegradation Extent (Bubble Size = Temperature °C)</b>"
    )
    fig.update_layout(
        template="plotly_white",
        xaxis_title="<b>Incubation Period (Days)</b>",
        yaxis_title="<b>Weight Loss (%)</b>",
        hoverlabel=dict(bgcolor="white", font_size=12),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


def plot_pretreatment_impact(df: pd.DataFrame) -> go.Figure:
    """Bar chart evaluating the impact of pretreatment methods on degradation percentage."""
    if df.empty:
        return go.Figure()

    summary = (
        df.groupby(["pretreatment_method", "plastic_abbreviation"])["weight_loss_percentage"]
        .mean()
        .reset_index()
    )

    fig = px.bar(
        summary,
        x="pretreatment_method",
        y="weight_loss_percentage",
        color="plastic_abbreviation",
        barmode="group",
        labels={
            "pretreatment_method": "Pretreatment Method",
            "weight_loss_percentage": "Mean Weight Loss (%)",
            "plastic_abbreviation": "Plastic"
        },
        title="<b>Impact of Substrate Pretreatment on Biodegradation Efficacy</b>"
    )
    fig.update_layout(
        template="plotly_white",
        xaxis_title="<b>Pretreatment Applied</b>",
        yaxis_title="<b>Mean Weight Loss (%)</b>",
        hoverlabel=dict(bgcolor="white", font_size=12),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


def plot_degradation_rates(df: pd.DataFrame) -> go.Figure:
    """Bar chart comparing daily degradation rates (%/day) across plastic types."""
    if df.empty:
        return go.Figure()

    fig = px.strip(
        df,
        x="plastic_abbreviation",
        y="percentage_per_day",
        color="evidence_quality",
        color_discrete_map={
            "HIGH": "#28a745",
            "MODERATE": "#17a2b8",
            "LOW": "#fd7e14",
            "UNVERIFIED": "#6c757d"
        },
        hover_data=["organism_name", "weight_loss_percentage", "incubation_duration_days"],
        labels={
            "plastic_abbreviation": "Plastic Type",
            "percentage_per_day": "Normalized Rate (%/day)",
            "evidence_quality": "Evidence Quality"
        },
        title="<b>Daily Normalized Degradation Rate (%/day) Across Plastic Types</b>",
        category_orders={"plastic_abbreviation": ["PET", "PE", "PP", "PS", "PLA", "PHA"]}
    )
    fig.update_layout(
        template="plotly_white",
        xaxis_title="<b>Plastic Polymer Type</b>",
        yaxis_title="<b>Normalized Rate (%/day)</b>",
        hoverlabel=dict(bgcolor="white", font_size=12),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


def plot_evidence_quality_distribution(df: pd.DataFrame) -> go.Figure:
    """Donut chart illustrating the breakdown of analytical evidence quality."""
    if df.empty:
        return go.Figure()

    counts = df["evidence_quality"].value_counts().reset_index()
    counts.columns = ["evidence_quality", "count"]

    color_map = {
        "HIGH": "#28a745",
        "MODERATE": "#17a2b8",
        "LOW": "#fd7e14",
        "UNVERIFIED": "#6c757d"
    }
    colors = [color_map.get(eq, "#333333") for eq in counts["evidence_quality"]]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=counts["evidence_quality"],
                values=counts["count"],
                hole=0.5,
                marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
                textinfo="label+percent+value",
                hoverinfo="label+value+percent"
            )
        ]
    )
    fig.update_layout(
        title="<b>Evidence-Quality Distribution (Analytical Rigor)</b>",
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    return fig


def plot_standards_distribution(df: pd.DataFrame) -> go.Figure:
    """Bar chart illustrating reported standard compliance."""
    if df.empty:
        return go.Figure()

    counts = df["standard_name"].value_counts().reset_index()
    counts.columns = ["standard_name", "count"]

    fig = px.bar(
        counts,
        x="standard_name",
        y="count",
        color="standard_name",
        labels={"standard_name": "Standard Framework", "count": "Trial Count"},
        title="<b>Reported Standards Utilization (ASTM / ISO / None)</b>"
    )
    fig.update_layout(
        template="plotly_white",
        xaxis_title="<b>Reported Testing Standard</b>",
        yaxis_title="<b>Number of Trials</b>",
        showlegend=False,
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig
