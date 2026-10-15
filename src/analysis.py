"""
Analysis & Statistics Module for Smart Waste Management.
Implements Functional Requirements FR-3:
- Descriptive statistics (mean, median fill level per zone and waste type)
- Fill-level distributions and category proportions
- Temporal trends and historical overflow analytics
"""

from typing import Dict, Any
import pandas as pd
import numpy as np


def compute_summary_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute high-level executive KPI metrics from latest bin readings.
    """
    if df.empty:
        return {
            "total_bins": 0,
            "critical_bins": 0,
            "high_bins": 0,
            "medium_bins": 0,
            "low_bins": 0,
            "overflow_bins": 0,
            "avg_fill": 0.0,
            "median_fill": 0.0,
            "most_critical_zone": "N/A"
        }

    total_bins = len(df)
    critical_count = int((df["fill_category"] == "Critical").sum())
    high_count = int((df["fill_category"] == "High").sum())
    medium_count = int((df["fill_category"] == "Medium").sum())
    low_count = int((df["fill_category"] == "Low").sum())
    overflow_count = int(df["overflow_status"].isin([True, 1, "True", "true"]).sum())
    avg_fill = float(df["fill_level"].mean())
    median_fill = float(df["fill_level"].median())

    # Find zone with highest average fill
    zone_means = df.groupby("location_name")["fill_level"].mean()
    most_critical_zone = str(zone_means.idxmax()) if not zone_means.empty else "N/A"

    return {
        "total_bins": total_bins,
        "critical_bins": critical_count,
        "high_bins": high_count,
        "medium_bins": medium_count,
        "low_bins": low_count,
        "overflow_bins": overflow_count,
        "avg_fill": round(avg_fill, 1),
        "median_fill": round(median_fill, 1),
        "most_critical_zone": most_critical_zone
    }


def compute_zone_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute mean, median, min, max, and overflow count per zone / location (FR-3.1).
    """
    if df.empty:
        return pd.DataFrame()

    stats = df.groupby("location_name").agg(
        total_bins=("bin_id", "count"),
        mean_fill=("fill_level", "mean"),
        median_fill=("fill_level", "median"),
        max_fill=("fill_level", "max"),
        overflow_incidents=("overflow_status", lambda x: int(x.isin([True, 1]).sum()))
    ).reset_index()

    stats["mean_fill"] = stats["mean_fill"].round(1)
    stats["median_fill"] = stats["median_fill"].round(1)
    stats["max_fill"] = stats["max_fill"].round(1)
    return stats.sort_values(by="mean_fill", ascending=False)


def compute_waste_type_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute bin counts and average fill levels by waste type (FR-3.3).
    """
    if df.empty:
        return pd.DataFrame()

    breakdown = df.groupby("waste_type").agg(
        bin_count=("bin_id", "count"),
        avg_fill=("fill_level", "mean"),
        overflow_count=("overflow_status", lambda x: int(x.isin([True, 1]).sum()))
    ).reset_index()

    breakdown["avg_fill"] = breakdown["avg_fill"].round(1)
    breakdown["percentage"] = (breakdown["bin_count"] / breakdown["bin_count"].sum() * 100).round(1)
    return breakdown


def compute_overflow_hotspots(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify locations with recurring overflow events (FR-3.5).
    """
    if df.empty:
        return pd.DataFrame()

    hotspots = df.groupby("location_name").agg(
        overflow_events=("overflow_status", lambda x: int(x.isin([True, 1]).sum())),
        avg_fill=("fill_level", "mean")
    ).reset_index()

    hotspots["avg_fill"] = hotspots["avg_fill"].round(1)
    return hotspots.sort_values(by=["overflow_events", "avg_fill"], ascending=[False, False])
