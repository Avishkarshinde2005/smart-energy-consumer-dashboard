"""
Forecasting Module for Smart Waste Management.
Implements Stretch Requirement FR-8 & TRD Section 5.4:
- Linear trend / rate-of-fill regression
- Predicts when a bin will cross Critical fill threshold (>= 86%)
- Flags predicted overflow timeframes (<6h, <12h, <24h)
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


def predict_bin_fill_trend(
    history_df: pd.DataFrame,
    bin_id: str,
    critical_threshold: float = 86.0
) -> Dict[str, Any]:
    """
    Fit a linear trend on historical fill levels for a specific bin
    to predict rate of fill and time remaining until Critical status.
    """
    bin_data = history_df[history_df["bin_id"] == bin_id].copy()
    if len(bin_data) < 2:
        return {
            "bin_id": bin_id,
            "current_fill": float(bin_data["fill_level"].iloc[-1]) if not bin_data.empty else 0.0,
            "hourly_rate": 0.0,
            "hours_to_critical": None,
            "urgency": "Insufficient Data"
        }

    bin_data["timestamp"] = pd.to_datetime(bin_data["timestamp"])
    bin_data = bin_data.sort_values("timestamp")

    # Filter out historical emptying drops (only look at the latest continuous accumulation phase)
    # If a drastic drop occurred (> 20%), start from that post-emptying timestamp
    drops = bin_data["fill_level"].diff() < -20.0
    if drops.any():
        last_drop_idx = bin_data[drops].index[-1]
        bin_data = bin_data.loc[last_drop_idx:]

    if len(bin_data) < 2:
        current_fill = float(bin_data["fill_level"].iloc[-1])
        return {
            "bin_id": bin_id,
            "current_fill": current_fill,
            "hourly_rate": 2.5,  # Heuristic average
            "hours_to_critical": max(0.0, round((critical_threshold - current_fill) / 2.5, 1)) if current_fill < critical_threshold else 0.0,
            "urgency": "Approximated"
        }

    # Time delta in hours from first observation
    t0 = bin_data["timestamp"].iloc[0]
    hours = (bin_data["timestamp"] - t0).dt.total_seconds() / 3600.0
    fills = bin_data["fill_level"].values

    # Fit linear slope: fill = slope * hours + intercept
    if hours.iloc[-1] > 0.05:
        poly = np.polyfit(hours, fills, 1)
        hourly_rate = max(0.2, float(poly[0]))  # Ensure positive accumulation rate
    else:
        hourly_rate = 2.0

    current_fill = float(fills[-1])

    if current_fill >= critical_threshold:
        hours_to_crit = 0.0
        urgency = "Immediate (Already Critical)"
    else:
        remaining_fill = critical_threshold - current_fill
        hours_to_crit = round(remaining_fill / hourly_rate, 1)
        if hours_to_crit <= 6.0:
            urgency = "High (Critical within 6h)"
        elif hours_to_crit <= 18.0:
            urgency = "Medium (Critical within 18h)"
        else:
            urgency = "Low (> 18h remaining)"

    return {
        "bin_id": bin_id,
        "location_name": bin_data["location_name"].iloc[-1] if "location_name" in bin_data.columns else f"Bin {bin_id}",
        "current_fill": current_fill,
        "hourly_rate": round(hourly_rate, 2),
        "hours_to_critical": hours_to_crit,
        "urgency": urgency
    }


def batch_forecast_all_bins(
    history_df: pd.DataFrame,
    critical_threshold: float = 86.0
) -> pd.DataFrame:
    """
    Run forecast model across all bins in the historical dataset.
    """
    if history_df.empty:
        return pd.DataFrame()

    results = []
    for b_id in history_df["bin_id"].unique():
        pred = predict_bin_fill_trend(history_df, b_id, critical_threshold)
        results.append(pred)

    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res = df_res.sort_values(by=["hours_to_critical", "current_fill"], ascending=[True, False]).reset_index(drop=True)
    return df_res
