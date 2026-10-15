"""
Unit tests for data preprocessing module (FR-1 & FR-2).
"""

import unittest
import pandas as pd
from src.preprocessing import categorize_fill_level, clean_and_preprocess


class TestPreprocessing(unittest.TestCase):
    def test_categorize_fill_level(self):
        self.assertEqual(categorize_fill_level(10.0), "Low")
        self.assertEqual(categorize_fill_level(25.0), "Low")
        self.assertEqual(categorize_fill_level(26.0), "Medium")
        self.assertEqual(categorize_fill_level(60.0), "Medium")
        self.assertEqual(categorize_fill_level(61.0), "High")
        self.assertEqual(categorize_fill_level(85.0), "High")
        self.assertEqual(categorize_fill_level(86.0), "Critical")
        self.assertEqual(categorize_fill_level(100.0), "Critical")

    def test_clean_and_preprocess_clipping(self):
        raw_data = pd.DataFrame([
            {"bin_id": "BIN-001", "fill_level": 140.0, "timestamp": "2026-09-01 10:00:00"},
            {"bin_id": "BIN-002", "fill_level": -25.0, "timestamp": "2026-09-01 10:00:00"}
        ])
        cleaned, report = clean_and_preprocess(raw_data)
        self.assertEqual(report["fill_clipped_count"], 2)
        self.assertEqual(cleaned.loc[cleaned["bin_id"] == "BIN-001", "fill_level"].values[0], 100.0)
        self.assertEqual(cleaned.loc[cleaned["bin_id"] == "BIN-002", "fill_level"].values[0], 0.0)

    def test_clean_and_preprocess_deduplication(self):
        raw_data = pd.DataFrame([
            {"bin_id": "BIN-001", "fill_level": 50.0, "timestamp": "2026-09-01 10:00:00"},
            {"bin_id": "BIN-001", "fill_level": 55.0, "timestamp": "2026-09-01 10:00:00"}
        ])
        cleaned, report = clean_and_preprocess(raw_data)
        self.assertEqual(report["duplicates_removed"], 1)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned["fill_level"].values[0], 55.0)

    def test_clean_and_preprocess_missing_mandatory(self):
        raw_data = pd.DataFrame([
            {"bin_id": "BIN-001", "fill_level": 40.0, "timestamp": "2026-09-01 10:00:00"},
            {"bin_id": None, "fill_level": 40.0, "timestamp": "2026-09-01 10:00:00"},
            {"bin_id": "BIN-003", "fill_level": None, "timestamp": "2026-09-01 10:00:00"}
        ])
        cleaned, report = clean_and_preprocess(raw_data)
        self.assertEqual(report["missing_mandatory_dropped"], 2)
        self.assertEqual(len(cleaned), 1)


if __name__ == "__main__":
    unittest.main()
