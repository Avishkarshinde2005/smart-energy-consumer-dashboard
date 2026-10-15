"""
Route Optimization Module for Smart Waste Management.
Implements Functional Requirements FR-5:
- Haversine distance matrix construction
- Nearest Neighbor heuristic (MVP)
- Google OR-Tools TSP solver (Enhanced)
- Route distance estimation and comparison against naive fixed-order routes
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from src.utils import haversine_distance, compute_distance_matrix

DEFAULT_DEPOT = {
    "bin_id": "DEPOT",
    "location_name": "Central Municipal Waste Depot",
    "latitude": 18.5204,
    "longitude": 73.8567
}


def calculate_total_route_distance(points: List[Tuple[float, float]], return_to_depot: bool = True) -> float:
    """
    Compute cumulative travel distance in kilometers through a sequence of (lat, lon) waypoints.
    """
    if len(points) < 2:
        return 0.0

    total_dist = 0.0
    for i in range(len(points) - 1):
        total_dist += haversine_distance(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])

    if return_to_depot and len(points) > 2:
        total_dist += haversine_distance(points[-1][0], points[-1][1], points[0][0], points[0][1])

    return round(total_dist, 3)


def solve_nearest_neighbor_tsp(
    depot: Dict[str, Any],
    bins: List[Dict[str, Any]],
    return_to_depot: bool = True
) -> Dict[str, Any]:
    """
    Solve TSP using the Nearest Neighbor greedy heuristic.
    Starting from the Depot, always choose the nearest unvisited priority bin.
    """
    if not bins:
        return {
            "route": [depot],
            "total_distance_km": 0.0,
            "method": "Nearest Neighbor (Empty)"
        }

    unvisited = list(bins)
    ordered_route = [depot]
    current_pos = (depot["latitude"], depot["longitude"])

    while unvisited:
        nearest_idx = -1
        nearest_dist = float("inf")

        for idx, candidate in enumerate(unvisited):
            dist = haversine_distance(
                current_pos[0], current_pos[1],
                candidate["latitude"], candidate["longitude"]
            )
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_idx = idx

        next_stop = unvisited.pop(nearest_idx)
        ordered_route.append(next_stop)
        current_pos = (next_stop["latitude"], next_stop["longitude"])

    if return_to_depot:
        ordered_route.append(depot)

    coords = [(p["latitude"], p["longitude"]) for p in ordered_route]
    total_km = calculate_total_route_distance(coords, return_to_depot=False)

    return {
        "route": ordered_route,
        "total_distance_km": total_km,
        "method": "Nearest Neighbor Heuristic"
    }


def solve_ortools_tsp(
    depot: Dict[str, Any],
    bins: List[Dict[str, Any]],
    return_to_depot: bool = True
) -> Dict[str, Any]:
    """
    Solve TSP using Google OR-Tools RoutingModel with PATH_CHEAPEST_ARC.
    Falls back gracefully to Nearest Neighbor if OR-Tools is unavailable.
    """
    if not bins:
        return solve_nearest_neighbor_tsp(depot, bins, return_to_depot)

    try:
        from ortools.constraint_solver import routing_enums_pb2
        from ortools.constraint_solver import pywrapcp

        all_nodes = [depot] + list(bins)
        num_nodes = len(all_nodes)

        # Scale distances to integers (meters) for OR-Tools solver
        distance_matrix = []
        for i in range(num_nodes):
            row = []
            for j in range(num_nodes):
                if i == j:
                    row.append(0)
                else:
                    dist_km = haversine_distance(
                        all_nodes[i]["latitude"], all_nodes[i]["longitude"],
                        all_nodes[j]["latitude"], all_nodes[j]["longitude"]
                    )
                    row.append(int(dist_km * 1000.0))  # in meters
            distance_matrix.append(row)

        manager = pywrapcp.RoutingIndexManager(num_nodes, 1, 0)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.time_limit.seconds = 3

        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            index = routing.Start(0)
            ordered_route = []
            while not routing.IsEnd(index):
                node_idx = manager.IndexToNode(index)
                ordered_route.append(all_nodes[node_idx])
                index = solution.Value(routing.NextVar(index))

            if return_to_depot:
                ordered_route.append(depot)

            coords = [(p["latitude"], p["longitude"]) for p in ordered_route]
            total_km = calculate_total_route_distance(coords, return_to_depot=False)

            return {
                "route": ordered_route,
                "total_distance_km": total_km,
                "method": "Google OR-Tools TSP Solver"
            }

    except Exception:
        pass

    # Fallback to Nearest Neighbor if OR-Tools not available or failed
    return solve_nearest_neighbor_tsp(depot, bins, return_to_depot)


def compare_routes(
    depot: Dict[str, Any],
    bins: List[Dict[str, Any]],
    optimized_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare optimized route against naive fixed-order (e.g. arbitrary catalog order) route.
    Implements FR-5.4.
    """
    naive_route = [depot] + list(bins) + [depot]
    naive_coords = [(p["latitude"], p["longitude"]) for p in naive_route]
    naive_distance_km = calculate_total_route_distance(naive_coords, return_to_depot=False)

    opt_distance_km = optimized_result["total_distance_km"]

    reduction_km = max(0.0, round(naive_distance_km - opt_distance_km, 3))
    reduction_pct = 0.0
    if naive_distance_km > 0:
        reduction_pct = round((reduction_km / naive_distance_km) * 100.0, 1)

    # Estimate fuel & emissions savings (average 0.25 liters of diesel per km)
    liters_saved = round(reduction_km * 0.25, 2)
    co2_kg_saved = round(liters_saved * 2.68, 2)  # ~2.68 kg CO2 per liter diesel

    return {
        "naive_distance_km": round(naive_distance_km, 3),
        "optimized_distance_km": round(opt_distance_km, 3),
        "distance_reduction_km": reduction_km,
        "distance_reduction_pct": reduction_pct,
        "estimated_fuel_saved_liters": liters_saved,
        "estimated_co2_avoided_kg": co2_kg_saved,
        "method": optimized_result.get("method", "Optimized")
    }
