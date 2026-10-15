"""
Data Loader Module for Smart Waste Management.
Supports:
- Synthetic dataset generation (College campus / municipal sector)
- Raw CSV / Google Form export loading
- Sample data provisioning
"""

import os
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import pandas as pd
import numpy as np

# Reference Depot & Campus Coordinates (e.g., University Campus Center)
BASE_LAT = 18.5204
BASE_LON = 73.8567

CAMPUS_ZONES = [
    ("Main Academic Block", 0.003, 0.002, "General", "Daily"),
    ("Engineering Complex", 0.005, -0.003, "Recyclable", "Daily"),
    ("Central Cafeteria", -0.002, 0.004, "Organic", "Daily"),
    ("Hostel Quadrangle A", -0.006, -0.005, "General", "Daily"),
    ("Hostel Quadrangle B", -0.007, -0.003, "General", "Alternate Days"),
    ("Science & Research Labs", 0.004, 0.006, "Hazardous", "Alternate Days"),
    ("Sports Arena & Gym", -0.004, 0.007, "Recyclable", "Daily"),
    ("Admin & Admissions Wing", 0.001, -0.002, "General", "Daily"),
    ("Campus Food Court", -0.003, 0.002, "Organic", "Daily"),
    ("Library & Study Center", 0.002, 0.004, "Recyclable", "Daily"),
    ("Mechanical Workshop", 0.006, -0.006, "Hazardous", "Bi-Weekly"),
    ("North Gate Entry", 0.008, 0.001, "General", "Daily"),
    ("South Gate & Parking", -0.008, 0.002, "General", "Daily"),
    ("Auditorium Plaza", -0.001, -0.004, "Recyclable", "Alternate Days"),
    ("Faculty Quarters", 0.003, -0.008, "Organic", "Daily")
]


def generate_synthetic_dataset(
    num_bins: int = 30,
    days_of_history: int = 5,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate realistic multi-day time-series bin readings for simulation and demonstration.
    """
    random.seed(seed)
    np.random.seed(seed)

    records = []
    base_time = datetime.now() - timedelta(days=days_of_history)

    bins_metadata = []
    for i in range(1, num_bins + 1):
        zone_info = CAMPUS_ZONES[(i - 1) % len(CAMPUS_ZONES)]
        zone_name = f"{zone_info[0]} - Bin #{i:02d}"
        
        # Add slight jitter to lat/long
        lat = BASE_LAT + zone_info[1] + random.uniform(-0.001, 0.001)
        lon = BASE_LON + zone_info[2] + random.uniform(-0.001, 0.001)
        waste_type = zone_info[3]
        freq = zone_info[4]

        # Base accumulation rate (% per hour)
        base_rate = random.uniform(1.8, 4.2)
        if "Cafeteria" in zone_name or "Food Court" in zone_name:
            base_rate *= 1.6  # Fills up much faster

        bins_metadata.append({
            "bin_id": f"BIN-{i:03d}",
            "location_name": zone_name,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "waste_type": waste_type,
            "collection_frequency": freq,
            "rate": base_rate
        })

    # Simulate readings over time
    for b in bins_metadata:
        curr_fill = random.uniform(10.0, 40.0)
        curr_time = base_time
        while curr_time <= datetime.now():
            # Add accumulation
            hours_passed = random.uniform(3.5, 6.0)
            curr_time += timedelta(hours=hours_passed)
            if curr_time > datetime.now():
                break

            curr_fill += b["rate"] * hours_passed + random.uniform(-3, 6)

            # Collection event if it was emptied previously
            if curr_fill > 95.0 and random.random() < 0.6:
                curr_fill = random.uniform(0.0, 15.0)

            fill_clipped = max(0.0, min(100.0, round(curr_fill, 1)))
            overflow = fill_clipped >= 90.0 or (fill_clipped >= 85.0 and random.random() < 0.3)

            records.append({
                "bin_id": b["bin_id"],
                "location_name": b["location_name"],
                "latitude": b["latitude"],
                "longitude": b["longitude"],
                "fill_level": fill_clipped,
                "waste_type": b["waste_type"],
                "collection_frequency": b["collection_frequency"],
                "overflow_status": overflow,
                "timestamp": curr_time.strftime("%Y-%m-%d %H:%M:%S")
            })

    df = pd.DataFrame(records)
    return df


def load_dataset_from_csv(filepath: str) -> pd.DataFrame:
    """
    Load raw or cleaned CSV file.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found at: {filepath}")
    return pd.read_csv(filepath)


def save_dataset_to_csv(df: pd.DataFrame, filepath: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    df.to_csv(filepath, index=False)
