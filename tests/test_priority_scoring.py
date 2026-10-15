"""
Unit tests for priority scoring module (FR-4).
"""

import unittest
import pandas as pd
from src.priority_scoring import calculate_rule_based_priority


class TestPriorityScoring(unittest.TestCase):
    def test_rule_based_scoring_formula(self):
        data = pd.DataFrame([
            {
                "bin_id": "BIN-001",
                "fill_level": 90.0,
                "overflow_status": True,
                "days_since_last_collection": 2.0,
                "fill_category": "Critical"
            },
            {
                "bin_id": "BIN-002",
                "fill_level": 20.0,
                "overflow_status": False,
                "days_since_last_collection": 1.0,
                "fill_category": "Low"
            }
        ])

        scored = calculate_rule_based_priority(
            data,
            fill_weight=0.5,
            overflow_weight=35.0,
            freq_weight=3.0,
            threshold_score=40.0
        )

        # BIN-001: 0.5*90 + 35*1 + 3*2 = 45 + 35 + 6 = 86.0
        # BIN-002: 0.5*20 + 35*0 + 3*1 = 10 + 0 + 3 = 13.0
        score1 = scored.loc[scored["bin_id"] == "BIN-001", "priority_score"].values[0]
        score2 = scored.loc[scored["bin_id"] == "BIN-002", "priority_score"].values[0]

        self.assertAlmostEqual(score1, 86.0, places=1)
        self.assertAlmostEqual(score2, 13.0, places=1)
        self.assertTrue(scored.loc[scored["bin_id"] == "BIN-001", "needs_collection"].values[0])
        self.assertFalse(scored.loc[scored["bin_id"] == "BIN-002", "needs_collection"].values[0])
        self.assertEqual(scored.loc[scored["bin_id"] == "BIN-001", "rank"].values[0], 1)


if __name__ == "__main__":
    unittest.main()
