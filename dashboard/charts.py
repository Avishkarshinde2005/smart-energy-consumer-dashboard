"""
Visualizations and Charts Module for Streamlit Dashboard.
Implements Functional Requirements FR-3 and FR-5.4:
- Fill-level distribution histogram
- Waste-type breakdown pie/donut chart
- Historical fill trend line chart
- Zone overflow hotspots bar chart
- Naive vs. Optimized route comparison bar chart
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


COLOR_MAP = {
    "Low": "#2e7d32",       # Green
    "Medium": "#1976d2",    # Blue
    "High": "#f57c00",      # Orange
    "Critical": "#d32f2f"   # Red
}


def plot_fill_distribution(df: pd.DataFrame) -> go.Figure:
    """
    Histogram of fill-level distribution (FR-3.2).
    """
    fig = px.histogram(
        df,
        x="fill_level",
        nbins=20,
        color="fill_category",
        color_discrete_map=COLOR_MAP,
        title="<b>Bin Fill-Level Distribution</b>",
        labels={"fill_level": "Fill Level (%)", "fill_category": "Fill Category"},
        template="plotly_white"
    )
    fig.update_layout(
        bargap=0.1,
        xaxis=dict(range=[0, 100], ticksuffix="%"),
        yaxis_title="Count of Bins",
        legend_title="Category",
        height=380,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def plot_waste_type_breakdown(df: pd.DataFrame) -> go.Figure:
    """
    Donut chart of waste-type proportions (FR-3.3).
    """
    breakdown = df["waste_type"].value_counts().reset_index()
    breakdown.columns = ["waste_type", "count"]

    fig = px.pie(
        breakdown,
        names="waste_type",
        values="count",
        hole=0.45,
        title="<b>Waste Stream Composition</b>",
        color_discrete_sequence=px.colors.qualitative.Prism,
        template="plotly_white"
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def plot_fill_trend_over_time(history_df: pd.DataFrame) -> go.Figure:
    """
    Line chart showing average fill level over time (FR-3.4).
    """
    if history_df.empty or "timestamp" not in history_df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No time-series data available", showarrow=False)
        return fig

    hist = history_df.copy()
    hist["timestamp"] = pd.to_datetime(hist["timestamp"])
    
    # Resample or group by 4-hour window
    grouped = hist.groupby([pd.Grouper(key="timestamp", freq="6h"), "waste_type"])["fill_level"].mean().reset_index()

    fig = px.line(
        grouped,
        x="timestamp",
        y="fill_level",
        color="waste_type",
        title="<b>Fill Level Temporal Trend by Waste Stream</b>",
        labels={"timestamp": "Time", "fill_level": "Average Fill (%)", "waste_type": "Waste Stream"},
        template="plotly_white",
        markers=True
    )
    fig.update_layout(
        yaxis=dict(range=[0, 100], ticksuffix="%"),
        height=400,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def plot_overflow_hotspots(df: pd.DataFrame) -> go.Figure:
    """
    Bar chart of overflow frequency by location / zone (FR-3.5).
    """
    zone_ovf = df.groupby("location_name").agg(
        overflow_count=("overflow_status", lambda x: int(x.isin([True, 1]).sum())),
        avg_fill=("fill_level", "mean")
    ).reset_index()

    zone_ovf = zone_ovf.sort_values(by="overflow_count", ascending=False).head(10)

    fig = px.bar(
        zone_ovf,
        x="overflow_count",
        y="location_name",
        orientation="h",
        color="avg_fill",
        color_continuous_scale="Reds",
        title="<b>Top Overflow Risk Zones</b>",
        labels={"overflow_count": "Overflow Incidents", "location_name": "Location", "avg_fill": "Avg Fill %"},
        template="plotly_white"
    )
    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        height=380,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def plot_route_comparison(route_metrics: dict) -> go.Figure:
    """
    Bar chart comparing Naive fixed-order route distance vs Optimized route distance (FR-5.4).
    """
    categories = ["Naive Sequence Route", "Optimized TSP Route"]
    distances = [
        route_metrics.get("naive_distance_km", 0.0),
        route_metrics.get("optimized_distance_km", 0.0)
    ]
    colors = ["#e57373", "#81c784"]

    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=distances,
            marker_color=colors,
            text=[f"{d:.2f} km" for d in distances],
            textposition="auto"
        )
    ])
    fig.update_layout(
        title="<b>Route Optimization Benchmark (Distance in km)</b>",
        yaxis_title="Total Distance (km)",
        template="plotly_white",
        height=360,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig
