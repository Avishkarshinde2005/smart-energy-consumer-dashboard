"""
Data Preprocessing Module for Smart Waste Management.
Implements Functional Requirements FR-1 and FR-2:
- Mandatory field validation
- Duplicate detection and removal
- Missing value imputation/handling
- Fill level bound clipping (0 to 100%)
- Fill level categorization (Low, Medium, High, Critical)
"""

from datetime import datetime
from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np


def categorize_fill_level(fill: float) -> str:
    """
    Categorize numerical fill level into 4 standard bins:
    - Low: 0 - 25%
    - Medium: 26 - 60%
    - High: 61 - 85%
    - Critical: 86 - 100%
    """
    if pd.isna(fill):
        return "Unknown"
    fill_val = float(fill)
    if fill_val <= 25.0:
        return "Low"
    elif fill_val <= 60.0:
        return "Medium"
    elif fill_val <= 85.0:
        return "High"
    else:
        return "Critical"


def clean_and_preprocess(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Clean raw bin readings dataframe and report statistics on dropped/imputed values.
    Returns (cleaned_df, report_metrics)
    """
    report = {
        "initial_rows": len(df),
        "missing_mandatory_dropped": 0,
        "duplicates_removed": 0,
        "fill_clipped_count": 0,
        "final_rows": 0
    }
    
    if df.empty:
        report["final_rows"] = 0
        return df, report

    data = df.copy()

    # Standardize column names (lowercase, stripped)
    data.columns = [str(c).strip().lower().replace(" ", "_") for c in data.columns]

    # Required field aliases mapping
    col_map = {
        "bin": "bin_id",
        "binid": "bin_id",
        "id": "bin_id",
        "location": "location_name",
        "area": "location_name",
        "lat": "latitude",
        "lon": "longitude",
        "long": "longitude",
        "fill": "fill_level",
        "fill_pct": "fill_level",
        "fill_%": "fill_level",
        "waste": "waste_type",
        "type": "waste_type",
        "frequency": "collection_frequency",
        "overflow": "overflow_status",
        "time": "timestamp",
        "date": "timestamp"
    }
    for old_col, new_col in col_map.items():
        if old_col in data.columns and new_col not in data.columns:
            data.rename(columns={old_col: new_col}, inplace=True)

    # Mandatory field check (FR-1.3: reject/flag records missing Bin ID or Fill Level)
    mandatory_cols = ["bin_id", "fill_level"]
    existing_mand = [c for c in mandatory_cols if c in data.columns]
    if len(existing_mand) < 2:
        # If mandatory columns missing entirely, return empty with error
        report["error"] = f"Missing mandatory columns: {[c for c in mandatory_cols if c not in data.columns]}"
        return pd.DataFrame(), report

    before_mand = len(data)
    data = data.dropna(subset=["bin_id", "fill_level"])
    report["missing_mandatory_dropped"] = before_mand - len(data)

    # Convert bin_id to string
    data["bin_id"] = data["bin_id"].astype(str).str.strip()

    # Fill level numeric conversion & bounds validation (FR-2.4: 0 to 100%)
    data["fill_level"] = pd.to_numeric(data["fill_level"], errors="coerce")
    data = data.dropna(subset=["fill_level"])

    clipped_mask = (data["fill_level"] > 100.0) | (data["fill_level"] < 0.0)
    report["fill_clipped_count"] = int(clipped_mask.sum())
    data["fill_level"] = data["fill_level"].clip(lower=0.0, upper=100.0)

    # Timestamp handling
    if "timestamp" not in data.columns or data["timestamp"].isna().all():
        data["timestamp"] = datetime.now().isoformat()
    else:
        data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce").fillna(pd.Timestamp.now())
        data["timestamp"] = data["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Detect and remove duplicates: Bin ID + Timestamp (FR-2.1)
    before_dup = len(data)
    data = data.drop_duplicates(subset=["bin_id", "timestamp"], keep="last")
    report["duplicates_removed"] = before_dup - len(data)

    # Impute optional fields (FR-2.2)
    if "location_name" not in data.columns:
        data["location_name"] = "Zone-" + data["bin_id"]
    else:
        data["location_name"] = data["location_name"].fillna("Unknown Zone")

    if "latitude" not in data.columns or data["latitude"].isna().all():
        data["latitude"] = 18.5204  # Default sample reference coord
    else:
        data["latitude"] = pd.to_numeric(data["latitude"], errors="coerce").fillna(18.5204)

    if "longitude" not in data.columns or data["longitude"].isna().all():
        data["longitude"] = 73.8567
    else:
        data["longitude"] = pd.to_numeric(data["longitude"], errors="coerce").fillna(73.8567)

    if "waste_type" not in data.columns:
        data["waste_type"] = "General"
    else:
        data["waste_type"] = data["waste_type"].fillna("General").astype(str).str.strip().str.title()

    if "collection_frequency" not in data.columns:
        data["collection_frequency"] = "Daily"
    else:
        data["collection_frequency"] = data["collection_frequency"].fillna("Daily")

    # Overflow status derivation & boolean normalization
    if "overflow_status" in data.columns:
        data["overflow_status"] = data["overflow_status"].apply(
            lambda x: True if str(x).strip().lower() in ["true", "1", "yes", "t", "overflow"] else False
        )
    else:
        data["overflow_status"] = False

    # Auto-flag overflow if fill level >= 90%
    data.loc[data["fill_level"] >= 90.0, "overflow_status"] = True

    # Categorize Fill Level (FR-2.3)
    data["fill_category"] = data["fill_level"].apply(categorize_fill_level)

    # Days since last collection estimation
    if "days_since_last_collection" not in data.columns:
        # Heuristic estimation based on frequency and fill level
        freq_factor = data["collection_frequency"].map({
            "Daily": 1.0,
            "Alternate Days": 2.0,
            "Bi-Weekly": 3.5,
            "Weekly": 7.0
        }).fillna(1.5)
        data["days_since_last_collection"] = (freq_factor * (data["fill_level"] / 60.0)).round(1)

    report["final_rows"] = len(data)
    return data.reset_index(drop=True), report
