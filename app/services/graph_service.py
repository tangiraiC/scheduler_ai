from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
import re
from typing import Any

import networkx as nx


class GraphConstructionError(Exception):
    pass


@dataclass
class AssignmentNode:
    node_id: str
    employee_name: str
    shift_id: str
    day: str
    time: str
    shift_label: str
    start_time: str
    end_time: str
    location: str | None
    required_skills: list[str]
    employee_skills: list[str]
    employee_max_shifts_per_week: int | None
    shift_max_staff: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GraphService:
    """
    Builds a conflict graph for workforce scheduling.

    Node:
        One feasible candidate assignment = (employee, shift)

    Edge:
        Two assignments conflict and cannot both be selected.
    """

    SHIFT_LABEL_RANGES = {
        "morning": ("08:00", "12:00"),
        "day": ("09:00", "17:00"),
        "afternoon": ("12:00", "17:00"),
        "evening": ("17:00", "22:00"),
        "night": ("22:00", "06:00"),
    }

    def build_graph(self, items: list[str]) -> dict[str, Any]:
        """
        Legacy graph builder retained for simple callers/tests that pass labels.
        The scheduling pipeline should use build_conflict_graph.
        """
        return {
            "nodes": [{"id": idx, "label": item} for idx, item in enumerate(items)],
            "edges": [],
        }

    def build_conflict_graph(self, normalized_data: dict[str, Any]) -> dict[str, Any]:
        try:
            employees = normalized_data.get("entities", {}).get("employees", [])
            shifts = normalized_data.get("entities", {}).get("shifts", [])
            constraints = normalized_data.get("constraints", {})
        except AttributeError as exc:
            raise GraphConstructionError(f"Invalid normalized_data structure: {exc}") from exc

        if not employees or not shifts:
            raise GraphConstructionError("Employees and shifts are required to build the graph.")

        graph = nx.Graph()
        constraints = {
            **constraints,
            "cannot_work_with_pairs": self._cannot_work_with_pairs(employees, constraints),
        }
        candidate_nodes: list[AssignmentNode] = []

        for employee in employees:
            for shift in shifts:
                if self._is_candidate_feasible(employee, shift):
                    node = self._make_assignment_node(employee, shift)
                    candidate_nodes.append(node)
                    graph.add_node(node.node_id, **node.to_dict())

        for left, right in combinations(candidate_nodes, 2):
            reason = self._get_conflict_reason(left, right, constraints)
            if reason is not None:
                graph.add_edge(left.node_id, right.node_id, reason=reason)

        return {
            "graph": graph,
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "nodes": [graph.nodes[node_id] for node_id in graph.nodes],
            "edges": [
                {
                    "source": source,
                    "target": target,
                    "reason": data.get("reason", "conflict"),
                }
                for source, target, data in graph.edges(data=True)
            ],
        }

    def _is_candidate_feasible(self, employee: dict[str, Any], shift: dict[str, Any]) -> bool:
        employee_skills = set(employee.get("skills", []))
        required_skills = set(shift.get("required_skills", []))
        availability = set(employee.get("availability", []))

        if availability and not self._matches_availability(shift, availability):
            return False

        return required_skills.issubset(employee_skills)

    def _make_assignment_node(
        self, employee: dict[str, Any], shift: dict[str, Any]
    ) -> AssignmentNode:
        employee_name = employee["name"]
        shift_id = shift["id"]
        start_time, end_time = self._shift_time_bounds(shift)

        return AssignmentNode(
            node_id=f"{employee_name}__{shift_id}",
            employee_name=employee_name,
            shift_id=shift_id,
            day=shift.get("day", ""),
            time=shift.get("time", ""),
            shift_label=shift.get("shift_label", ""),
            start_time=start_time,
            end_time=end_time,
            location=shift.get("location"),
            required_skills=shift.get("required_skills", []),
            employee_skills=employee.get("skills", []),
            employee_max_shifts_per_week=employee.get("max_shifts_per_week"),
            shift_max_staff=shift.get("max_staff", 1),
        )

    def _get_conflict_reason(
        self,
        left: AssignmentNode,
        right: AssignmentNode,
        constraints: dict[str, Any],
    ) -> str | None:
        if left.employee_name == right.employee_name:
            if left.shift_id == right.shift_id:
                return "duplicate_employee_same_shift"

            need_travel = bool(left.location and right.location and left.location != right.location)

            if self._same_day(left.day, right.day) and self._times_overlap(
                left.start_time, left.end_time, right.start_time, right.end_time, need_travel
            ):
                return "employee_time_overlap"

        if self._cannot_work_together(left.employee_name, right.employee_name, constraints):
            if self._same_day(left.day, right.day) and self._times_overlap(
                left.start_time, left.end_time, right.start_time, right.end_time
            ):
                return "cannot_work_with"

        return None

    def _cannot_work_together(
        self,
        employee_a: str,
        employee_b: str,
        constraints: dict[str, Any],
    ) -> bool:
        pair_exclusions = constraints.get("cannot_work_with_pairs", [])
        normalized_pairs = {
            tuple(sorted([pair[0], pair[1]]))
            for pair in pair_exclusions
            if isinstance(pair, list) and len(pair) == 2
        }
        return tuple(sorted([employee_a, employee_b])) in normalized_pairs

    def _cannot_work_with_pairs(
        self,
        employees: list[dict[str, Any]],
        constraints: dict[str, Any],
    ) -> list[list[str]]:
        pairs = list(constraints.get("cannot_work_with_pairs", []))
        for employee in employees:
            employee_name = employee.get("name")
            if not employee_name:
                continue
            for blocked_name in employee.get("cannot_work_with", []):
                pairs.append([employee_name, blocked_name])
        return pairs

    def _matches_availability(self, shift: dict[str, Any], availability: set[str]) -> bool:
        day = shift.get("day", "")
        time = shift.get("time", "")
        shift_label = shift.get("shift_label", "")
        candidates = {day, f"{day}_{time}", f"{day}_{shift_label}"}
        return bool(availability.intersection(candidate for candidate in candidates if candidate))

    def _shift_time_bounds(self, shift: dict[str, Any]) -> tuple[str, str]:
        start_time = shift.get("start_time", "")
        end_time = shift.get("end_time", "")
        if start_time and end_time:
            return start_time, end_time

        time = shift.get("time", "")
        parsed = self._parse_time_range(time)
        if parsed is not None:
            return parsed

        shift_label = shift.get("shift_label") or time
        return self.SHIFT_LABEL_RANGES.get(shift_label, ("", ""))

    def _parse_time_range(self, value: str) -> tuple[str, str] | None:
        if not value:
            return None

        parts = re.split(r"\s*-\s*", value, maxsplit=1)
        if len(parts) != 2:
            return None

        start = self._normalize_clock(parts[0])
        end = self._normalize_clock(parts[1])
        if not start or not end:
            return None

        return start, end

    def _normalize_clock(self, value: str) -> str:
        match = re.fullmatch(r"(\d{1,2})(?::?(\d{2}))?", value.strip())
        if not match:
            return ""

        hour = int(match.group(1))
        minute = int(match.group(2) or "0")
        if hour > 23 or minute > 59:
            return ""

        return f"{hour:02d}:{minute:02d}"

    def _same_day(self, day_a: str, day_b: str) -> bool:
        return (day_a or "").strip().lower() == (day_b or "").strip().lower()

    def _times_overlap(
        self,
        start_a: str,
        end_a: str,
        start_b: str,
        end_b: str,
        need_travel: bool = False,
    ) -> bool:
        if not all([start_a, end_a, start_b, end_b]):
            return False

        range_a = self._time_range_to_minutes(start_a, end_a)
        range_b = self._time_range_to_minutes(start_b, end_b)

        buffer = 30 if need_travel else 0

        for a_start, a_end in range_a:
            for b_start, b_end in range_b:
                if max(a_start, b_start) < min(a_end, b_end):
                    return True
                if a_end <= b_start and (b_start - a_end) < buffer:
                    return True
                if b_end <= a_start and (a_start - b_end) < buffer:
                    return True

        return False

    def _time_range_to_minutes(self, start: str, end: str) -> list[tuple[int, int]]:
        start_minutes = self._clock_to_minutes(start)
        end_minutes = self._clock_to_minutes(end)

        if start_minutes < end_minutes:
            return [(start_minutes, end_minutes)]

        return [(start_minutes, 24 * 60), (0, end_minutes)]

    def _clock_to_minutes(self, value: str) -> int:
        hours, minutes = value.split(":", maxsplit=1)
        return int(hours) * 60 + int(minutes)
