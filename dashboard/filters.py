"""
Sidebar Filters and Control Widgets for Streamlit Dashboard.
Implements FR-6.2: Filtering by date range, zone, or waste type.
"""

from datetime import datetime, date
from typing import Dict, Any, Tuple
import pandas as pd
import streamlit as st


def render_sidebar_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Render sidebar filter controls and return filtered DataFrame plus filter parameter dict.
    """
    st.sidebar.title("Fleet Controls & Filters")
    st.sidebar.caption("Smart Waste Collection Management")

    if df.empty:
        return df, {}

    # 1. Zone / Location Filter
    all_zones = sorted(df["location_name"].dropna().unique().tolist())
    selected_zones = st.sidebar.multiselect(
        "Select Zones / Locations",
        options=all_zones,
        default=all_zones[:8] if len(all_zones) > 8 else all_zones,
        help="Filter bins by campus or municipal sector"
    )

    # 2. Waste Type Filter
    all_waste_types = sorted(df["waste_type"].dropna().unique().tolist())
    selected_waste_types = st.sidebar.multiselect(
        "Waste Types",
        options=all_waste_types,
        default=all_waste_types,
        help="Select waste streams to inspect"
    )

    # 3. Fill Category Filter
    all_cats = ["Low", "Medium", "High", "Critical"]
    existing_cats = [c for c in all_cats if c in df["fill_category"].unique()]
    selected_cats = st.sidebar.multiselect(
        "Fill Categories",
        options=existing_cats,
        default=existing_cats
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Optimization Parameters")

    # 4. Priority Score Threshold Slider
    priority_threshold = st.sidebar.slider(
        "Priority Threshold Score",
        min_value=20.0,
        max_value=90.0,
        value=40.0,
        step=5.0,
        help="Bins with priority score >= threshold are flagged for immediate pickup"
    )

    # 5. Routing Algorithm Selection
    routing_algo = st.sidebar.radio(
        "Routing Algorithm",
        options=["Google OR-Tools TSP", "Nearest Neighbor Heuristic"],
        index=0,
        help="Compare algorithmic solutions"
    )

    # 6. Include Return to Depot
    return_to_depot = st.sidebar.checkbox("Return to Depot after pickup", value=True)

    # Apply filters
    filtered_df = df.copy()
    if selected_zones:
        filtered_df = filtered_df[filtered_df["location_name"].isin(selected_zones)]
    if selected_waste_types:
        filtered_df = filtered_df[filtered_df["waste_type"].isin(selected_waste_types)]
    if selected_cats:
        filtered_df = filtered_df[filtered_df["fill_category"].isin(selected_cats)]

    params = {
        "selected_zones": selected_zones,
        "selected_waste_types": selected_waste_types,
        "selected_cats": selected_cats,
        "priority_threshold": priority_threshold,
        "routing_algo": routing_algo,
        "return_to_depot": return_to_depot
    }

    return filtered_df, params
