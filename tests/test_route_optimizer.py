"""
Unit tests for route optimization and Haversine distance (FR-5).
"""

import unittest
from src.utils import haversine_distance
from src.route_optimizer import solve_nearest_neighbor_tsp, compare_routes, DEFAULT_DEPOT


class TestRouteOptimizer(unittest.TestCase):
    def test_haversine_known_distance(self):
        # Pune to Mumbai ~120 km
        pune_lat, pune_lon = 18.5204, 73.8567
        mumbai_lat, mumbai_lon = 18.9220, 72.8347
        dist = haversine_distance(pune_lat, pune_lon, mumbai_lat, mumbai_lon)
        self.assertTrue(110.0 <= dist <= 130.0)

    def test_nearest_neighbor_tsp(self):
        depot = {"bin_id": "DEPOT", "latitude": 18.5204, "longitude": 73.8567}
        bins = [
            {"bin_id": "BIN-001", "latitude": 18.5210, "longitude": 73.8570},
            {"bin_id": "BIN-002", "latitude": 18.5250, "longitude": 73.8600},
            {"bin_id": "BIN-003", "latitude": 18.5215, "longitude": 73.8575}
        ]
        result = solve_nearest_neighbor_tsp(depot, bins, return_to_depot=True)
        self.assertIn("route", result)
        self.assertEqual(len(result["route"]), 5)  # Depot + 3 bins + Depot
        self.assertGreater(result["total_distance_km"], 0.0)

    def test_compare_routes(self):
        depot = {"bin_id": "DEPOT", "latitude": 18.5204, "longitude": 73.8567}
        bins = [
            {"bin_id": "BIN-001", "latitude": 18.5210, "longitude": 73.8570},
            {"bin_id": "BIN-002", "latitude": 18.5280, "longitude": 73.8650},
            {"bin_id": "BIN-003", "latitude": 18.5212, "longitude": 73.8572}
        ]
        opt_res = solve_nearest_neighbor_tsp(depot, bins, return_to_depot=True)
        comp = compare_routes(depot, bins, opt_res)
        self.assertIn("naive_distance_km", comp)
        self.assertIn("optimized_distance_km", comp)
        self.assertGreaterEqual(comp["naive_distance_km"], comp["optimized_distance_km"])


if __name__ == "__main__":
    unittest.main()
