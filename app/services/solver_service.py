from __future__ import annotations

from typing import Any

import networkx as nx

from app.services.graph_serializer import serialize_graph
from app.services.graph_service import GraphService


class SolverServiceError(Exception):
    pass


class SolverService:
    """
    Coloring-based scheduling engine.

    This service turns normalized scheduling constraints into a conflict graph,
    colors that graph with NetworkX, and builds a schedule-shaped candidate.
    Validation is handled by ScheduleService through ValidationService.
    """

    SUPPORTED_STRATEGIES = {
        "largest_first",
        "random_sequential",
        "smallest_last",
        "independent_set",
        "connected_sequential_bfs",
        "connected_sequential_dfs",
        "connected_sequential",
        "saturation_largest_first",
        "DSATUR",
    }

    def __init__(self) -> None:
        self.graph_service = GraphService()

    def solve(
        self,
        normalized_data: dict[str, Any],
        strategy: str = "largest_first",
    ) -> dict[str, Any]:
        if strategy not in self.SUPPORTED_STRATEGIES:
            raise SolverServiceError(
                f"Unsupported coloring strategy '{strategy}'. "
                f"Supported strategies: {sorted(self.SUPPORTED_STRATEGIES)}"
            )

        graph_result = self.graph_service.build_conflict_graph(normalized_data)
        graph: nx.Graph = graph_result["graph"]

        if graph.number_of_nodes() == 0:
            raise SolverServiceError("Conflict graph has no feasible assignment nodes.")

        coloring = self.greedy_color(graph, strategy=strategy)
        color_to_time_slot = self.map_colors_to_time_slots(graph, coloring)
        selected_assignments = self.select_assignments_from_coloring(graph, coloring)
        final_schedule = self.build_schedule_output(selected_assignments, color_to_time_slot)
        serialized_graph = serialize_graph(graph)

        return {
            "strategy": strategy,
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "color_count": len(set(coloring.values())) if coloring else 0,
            "coloring": coloring,
            "color_to_time_slot": color_to_time_slot,
            "selected_assignments": selected_assignments,
            "schedule": final_schedule,
            "graph": serialized_graph,
            "nodes": serialized_graph["nodes"],
            "edges": serialized_graph["edges"],
            "meta": serialized_graph["meta"],
        }

    def greedy_color(
        self,
        graph: nx.Graph,
        strategy: str = "largest_first",
    ) -> dict[str, int]:
        try:
            return nx.coloring.greedy_color(graph, strategy=strategy)
        except Exception as exc:
            raise SolverServiceError(
                f"Coloring failed with strategy '{strategy}': {exc}"
            ) from exc

    def compare_strategies(
        self,
        normalized_data: dict[str, Any],
        strategies: list[str] | None = None,
    ) -> dict[str, Any]:
        graph_result = self.graph_service.build_conflict_graph(normalized_data)
        graph: nx.Graph = graph_result["graph"]

        if graph.number_of_nodes() == 0:
            raise SolverServiceError("Conflict graph has no feasible assignment nodes.")

        candidate_strategies = strategies or [
            "largest_first",
            "saturation_largest_first",
        ]

        results = []
        for strategy in candidate_strategies:
            if strategy not in self.SUPPORTED_STRATEGIES:
                continue

            coloring = self.greedy_color(graph, strategy=strategy)
            color_count = len(set(coloring.values())) if coloring else 0

            results.append(
                {
                    "strategy": strategy,
                    "color_count": color_count,
                    "coloring": coloring,
                }
            )

        results = sorted(results, key=lambda item: item["color_count"])
        best = results[0] if results else None

        return {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "results": results,
            "best_strategy": best["strategy"] if best else None,
            "best_color_count": best["color_count"] if best else None,
        }

    def map_colors_to_time_slots(
        self,
        graph: nx.Graph,
        coloring: dict[str, int],
    ) -> dict[int, dict[str, Any]]:
        color_to_nodes: dict[int, list[str]] = {}
        for node_id, color in coloring.items():
            color_to_nodes.setdefault(color, []).append(node_id)

        color_to_time_slot: dict[int, dict[str, Any]] = {}
        for color, node_ids in sorted(color_to_nodes.items()):
            sample_node = graph.nodes[node_ids[0]]
            color_to_time_slot[color] = {
                "slot_label": f"slot_{color}",
                "day": sample_node.get("day"),
                "start_time": sample_node.get("start_time"),
                "end_time": sample_node.get("end_time"),
                "assignments": sorted(node_ids),
            }

        return color_to_time_slot

    def select_assignments_from_coloring(
        self,
        graph: nx.Graph,
        coloring: dict[str, int],
    ) -> list[dict[str, Any]]:
        shift_to_candidates: dict[str, list[tuple[str, dict[str, Any], int]]] = {}

        for node_id, color in coloring.items():
            attrs = dict(graph.nodes[node_id])
            shift_id = attrs["shift_id"]
            shift_to_candidates.setdefault(shift_id, []).append((node_id, attrs, color))

        selected = []
        selected_node_ids: set[str] = set()
        employee_assignment_counts: dict[str, int] = {}
        for shift_id in sorted(shift_to_candidates):
            candidates = shift_to_candidates[shift_id]
            max_staff = candidates[0][1].get("shift_max_staff", 1)
            assigned_count = 0

            while assigned_count < max_staff and candidates:
                ranked = sorted(
                    candidates,
                    key=lambda item: self._candidate_rank(item, employee_assignment_counts),
                )
                chosen = self._first_non_conflicting_candidate(
                    graph,
                    ranked,
                    selected_node_ids,
                    employee_assignment_counts,
                )
                if chosen is None:
                    break

                chosen_node_id, attrs, color = chosen
                selected_node_ids.add(chosen_node_id)
                employee_name = attrs["employee_name"]
                employee_assignment_counts[employee_name] = (
                    employee_assignment_counts.get(employee_name, 0) + 1
                )
                selected.append(
                    {
                        "node_id": chosen_node_id,
                        "employee_name": attrs["employee_name"],
                        "shift_id": attrs["shift_id"],
                        "day": attrs.get("day"),
                        "start_time": attrs.get("start_time"),
                        "end_time": attrs.get("end_time"),
                        "location": attrs.get("location"),
                        "required_skills": attrs.get("required_skills", []),
                        "employee_skills": attrs.get("employee_skills", []),
                        "color": color,
                    }
                )
                candidates = [c for c in candidates if c[0] != chosen_node_id]
                assigned_count += 1

        return sorted(
            selected,
            key=lambda item: (
                item.get("day") or "",
                item.get("start_time") or "",
                item["shift_id"],
            ),
        )

    def build_schedule_output(
        self,
        selected_assignments: list[dict[str, Any]],
        color_to_time_slot: dict[int, dict[str, Any]],
    ) -> dict[str, Any]:
        by_day: dict[str, list[dict[str, Any]]] = {}

        for item in selected_assignments:
            day = item.get("day") or "unknown"
            by_day.setdefault(day, []).append(
                {
                    "shift_id": item["shift_id"],
                    "employee_name": item["employee_name"],
                    "start_time": item["start_time"],
                    "end_time": item["end_time"],
                    "location": item["location"],
                    "color": item["color"],
                    "slot_label": color_to_time_slot[item["color"]]["slot_label"],
                }
            )

        for day in by_day:
            by_day[day] = sorted(
                by_day[day],
                key=lambda item: (item.get("start_time") or "", item["shift_id"]),
            )

        return {
            "days": by_day,
            "total_assignments": len(selected_assignments),
        }

    def _first_non_conflicting_candidate(
        self,
        graph: nx.Graph,
        candidates: list[tuple[str, dict[str, Any], int]],
        selected_node_ids: set[str],
        employee_assignment_counts: dict[str, int],
    ) -> tuple[str, dict[str, Any], int] | None:
        for node_id, attrs, color in candidates:
            if self._would_exceed_max_shifts(attrs, employee_assignment_counts):
                continue

            if all(
                not graph.has_edge(node_id, selected_node_id)
                for selected_node_id in selected_node_ids
            ):
                return node_id, attrs, color
        return None

    def _candidate_rank(
        self,
        candidate: tuple[str, dict[str, Any], int],
        employee_assignment_counts: dict[str, int],
    ) -> tuple[int, int, str]:
        node_id, attrs, color = candidate
        employee_name = attrs["employee_name"]
        assigned_count = employee_assignment_counts.get(employee_name, 0)
        return assigned_count, color, node_id

    def _would_exceed_max_shifts(
        self,
        attrs: dict[str, Any],
        employee_assignment_counts: dict[str, int],
    ) -> bool:
        max_shifts = attrs.get("employee_max_shifts_per_week")
        if max_shifts is None:
            return False

        employee_name = attrs["employee_name"]
        return employee_assignment_counts.get(employee_name, 0) + 1 > max_shifts
