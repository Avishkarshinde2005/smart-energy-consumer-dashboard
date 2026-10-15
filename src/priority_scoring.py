"""
Priority Scoring Module for Smart Waste Management.
Implements Functional Requirements FR-4:
- Rule-based priority scoring calculation
- Machine Learning priority classification (Random Forest)
- Ranking and filtering for daily collection queue
"""

import os
import pickle
from typing import Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np

# Default weights from TRD Section 5.1
DEFAULT_FILL_WEIGHT = 0.50
DEFAULT_OVERFLOW_WEIGHT = 35.0
DEFAULT_FREQ_WEIGHT = 3.0

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models", "priority_classifier.pkl"
)


def calculate_rule_based_priority(
    df: pd.DataFrame,
    fill_weight: float = DEFAULT_FILL_WEIGHT,
    overflow_weight: float = DEFAULT_OVERFLOW_WEIGHT,
    freq_weight: float = DEFAULT_FREQ_WEIGHT,
    threshold_score: float = 40.0
) -> pd.DataFrame:
    """
    Compute rule-based collection priority score:
        score = (w_fill * fill_level) + (w_overflow * overflow_status) + (w_freq * days_since_last_collection)
    Bins are ranked descending.
    """
    if df.empty:
        return df

    result = df.copy()

    # Numeric overflow binary
    overflow_bin = result["overflow_status"].apply(
        lambda x: 1.0 if x in [True, 1, "True", "true"] else 0.0
    )

    # Days since collection fallback
    if "days_since_last_collection" not in result.columns:
        result["days_since_last_collection"] = 1.0
    days_clean = result["days_since_last_collection"].fillna(1.0).astype(float)

    # Compute raw score
    result["priority_score"] = (
        (fill_weight * result["fill_level"].astype(float)) +
        (overflow_weight * overflow_bin) +
        (freq_weight * days_clean)
    ).round(2)

    # Flag for collection (needs_collection = True if score >= threshold or fill_category == Critical)
    result["needs_collection"] = (
        (result["priority_score"] >= threshold_score) |
        (result["fill_category"] == "Critical") |
        (overflow_bin == 1.0)
    )

    # Sort descending by priority score
    result = result.sort_values(by=["priority_score", "fill_level"], ascending=[False, False]).reset_index(drop=True)
    result["rank"] = range(1, len(result) + 1)

    return result


def train_ml_priority_classifier(df: pd.DataFrame, save_path: str = MODEL_PATH) -> Optional[Any]:
    """
    Train a Random Forest Classifier on historical bin data.
    Features: fill_level, days_since_last_collection, waste_type encoded, overflow_history
    """
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder

        data = df.copy()
        le = LabelEncoder()
        data["waste_type_enc"] = le.fit_transform(data["waste_type"].fillna("General").astype(str))

        if "historical_overflow_rate" not in data.columns:
            # Derive synthetic rate based on location or overflow status
            data["historical_overflow_rate"] = (data["fill_level"] / 100.0) * 0.3

        features = ["fill_level", "days_since_last_collection", "waste_type_enc", "historical_overflow_rate"]
        X = data[features].fillna(0)

        # Ground truth label: 1 if Critical or overflow or fill >= 75%
        y = (
            (data["fill_level"] >= 75.0) |
            (data["overflow_status"].isin([True, 1])) |
            (data.get("fill_category") == "Critical")
        ).astype(int)

        model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
        model.fit(X, y)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        payload = {"model": model, "label_encoder": le, "features": features}
        with open(save_path, "wb") as f:
            pickle.dump(payload, f)

        return payload

    except ImportError:
        # scikit-learn not available yet; save lightweight dummy model dictionary
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        payload = {"model": None, "type": "rule_based_fallback"}
        with open(save_path, "wb") as f:
            pickle.dump(payload, f)
        return payload


def predict_ml_priority(df: pd.DataFrame, model_path: str = MODEL_PATH) -> pd.DataFrame:
    """
    Predict collection need using the saved Random Forest model.
    Falls back to rule-based calculation if model or sklearn is unavailable.
    """
    if df.empty:
        return df

    if os.path.exists(model_path):
        try:
            with open(model_path, "rb") as f:
                payload = pickle.load(f)

            model = payload.get("model")
            le = payload.get("label_encoder")
            if model is not None and le is not None:
                data = df.copy()
                # Handle unseen labels gracefully
                data["waste_type_enc"] = data["waste_type"].apply(
                    lambda x: le.transform([x])[0] if x in le.classes_ else 0
                )
                if "historical_overflow_rate" not in data.columns:
                    data["historical_overflow_rate"] = (data["fill_level"] / 100.0) * 0.3

                X = data[payload["features"]].fillna(0)
                probs = model.predict_proba(X)[:, 1]
                data["ml_priority_prob"] = (probs * 100.0).round(1)
                data["priority_score"] = data["ml_priority_prob"]
                data["needs_collection"] = model.predict(X).astype(bool)
                data = data.sort_values(by="priority_score", ascending=False).reset_index(drop=True)
                data["rank"] = range(1, len(data) + 1)
                return data
        except Exception:
            pass

    # Fallback
    return calculate_rule_based_priority(df)
