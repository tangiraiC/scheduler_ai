from __future__ import annotations

from collections import defaultdict
from typing import Any


class ValidationServiceError(Exception):
    pass


class ValidationService:
    """
    Validates the schedule produced by the scheduling engine.

    Checks:
    1. Direct assignment conflicts
    2. Hard constraints
    3. Capacity and staffing limits
    """

    SHIFT_LABEL_RANGES = {
        "morning": ("08:00", "12:00"),
        "day": ("09:00", "17:00"),
        "afternoon": ("12:00", "17:00"),
        "evening": ("17:00", "22:00"),
        "night": ("22:00", "06:00"),
    }

    def validate(
        self,
        normalized_data: dict[str, Any],
        schedule_result: dict[str, Any],
    ) -> dict[str, Any]:
        entities = normalized_data.get("entities", {})
        constraints = normalized_data.get("constraints", {})

        employees = entities.get("employees", [])
        shifts = entities.get("shifts", [])
        selected_assignments = schedule_result.get("selected_assignments", [])

        employee_lookup = {employee["name"]: employee for employee in employees}
        shift_lookup = {shift["id"]: shift for shift in shifts}

        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        errors.extend(self.detect_conflicts(selected_assignments=selected_assignments))
        errors.extend(
            self.check_hard_constraints(
                selected_assignments=selected_assignments,
                employee_lookup=employee_lookup,
                shift_lookup=shift_lookup,
                constraints=constraints,
            )
        )
        errors.extend(
            self.validate_capacity_and_limits(
                selected_assignments=selected_assignments,
                shift_lookup=shift_lookup,
            )
        )
        errors.extend(
            self._check_max_shifts_per_employee(
                selected_assignments=selected_assignments,
                employee_lookup=employee_lookup,
            )
        )

        return {
            "is_valid": len(errors) == 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
        }

    def detect_conflicts(
        self,
        selected_assignments: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []

        grouped_by_employee: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for assignment in selected_assignments:
            grouped_by_employee[assignment["employee_name"]].append(assignment)

        for employee_name, assignments in grouped_by_employee.items():
            assignments = sorted(
                assignments,
                key=lambda item: (
                    item.get("day", ""),
                    item.get("start_time", ""),
                    item.get("shift_id", ""),
                ),
            )

            for index, assignment_a in enumerate(assignments):
                for assignment_b in assignments[index + 1 :]:
                    if self._same_day(
                        assignment_a.get("day"), assignment_b.get("day")
                    ) and self._times_overlap(
                        assignment_a.get("start_time"),
                        assignment_a.get("end_time"),
                        assignment_b.get("start_time"),
                        assignment_b.get("end_time"),
                    ):
                        errors.append(
                            {
                                "type": "employee_time_overlap",
                                "employee_name": employee_name,
                                "assignment_a": assignment_a["shift_id"],
                                "assignment_b": assignment_b["shift_id"],
                                "message": (
                                    f"{employee_name} is assigned to overlapping shifts "
                                    f"{assignment_a['shift_id']} and {assignment_b['shift_id']}."
                                ),
                            }
                        )

        return errors

    def check_hard_constraints(
        self,
        selected_assignments: list[dict[str, Any]],
        employee_lookup: dict[str, dict[str, Any]],
        shift_lookup: dict[str, dict[str, Any]],
        constraints: dict[str, Any],
    ) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []

        for assignment in selected_assignments:
            employee_name = assignment["employee_name"]
            shift_id = assignment["shift_id"]

            employee = employee_lookup.get(employee_name)
            shift = shift_lookup.get(shift_id)

            if not employee or not shift:
                errors.append(
                    {
                        "type": "missing_reference",
                        "employee_name": employee_name,
                        "shift_id": shift_id,
                        "message": (
                            "Missing employee or shift reference for assignment "
                            f"{employee_name} -> {shift_id}."
                        ),
                    }
                )
                continue

            if not self._matches_availability(employee, shift):
                errors.append(
                    {
                        "type": "availability_violation",
                        "employee_name": employee_name,
                        "shift_id": shift_id,
                        "message": (
                            f"{employee_name} is assigned to {shift_id}, "
                            "but is not available for that shift."
                        ),
                    }
                )

            employee_skills = set(employee.get("skills", []))
            required_skills = set(shift.get("required_skills", []))
            missing_skills = sorted(required_skills - employee_skills)
            if missing_skills:
                errors.append(
                    {
                        "type": "skill_violation",
                        "employee_name": employee_name,
                        "shift_id": shift_id,
                        "missing_skills": missing_skills,
                        "message": (
                            f"{employee_name} does not satisfy required skills "
                            f"for {shift_id}: {missing_skills}."
                        ),
                    }
                )

        hard_constraints = constraints.get("hard_constraints", [])
        if "max_40_hours_per_7_days" in hard_constraints:
            errors.extend(
                self._check_max_hours_per_employee(
                    selected_assignments=selected_assignments
                )
            )

        errors.extend(
            self._check_cannot_work_with_pairs(
                selected_assignments=selected_assignments,
                employee_lookup=employee_lookup,
                constraints=constraints,
            )
        )

        return errors

    def validate_capacity_and_limits(
        self,
        selected_assignments: list[dict[str, Any]],
        shift_lookup: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []

        shift_assignment_counts: dict[str, int] = defaultdict(int)
        for assignment in selected_assignments:
            shift_assignment_counts[assignment["shift_id"]] += 1

        for shift_id, shift in shift_lookup.items():
            assigned_count = shift_assignment_counts.get(shift_id, 0)
            min_staff = shift.get("min_staff", 1)
            max_staff = shift.get("max_staff", 1)

            if assigned_count < min_staff:
                errors.append(
                    {
                        "type": "understaffed_shift",
                        "shift_id": shift_id,
                        "assigned_count": assigned_count,
                        "min_staff": min_staff,
                        "message": (
                            f"{shift_id} is understaffed: assigned {assigned_count}, "
                            f"requires at least {min_staff}."
                        ),
                    }
                )

            if assigned_count > max_staff:
                errors.append(
                    {
                        "type": "overstaffed_shift",
                        "shift_id": shift_id,
                        "assigned_count": assigned_count,
                        "max_staff": max_staff,
                        "message": (
                            f"{shift_id} exceeds max staffing: assigned {assigned_count}, "
                            f"max is {max_staff}."
                        ),
                    }
                )

        return errors

    def _check_max_hours_per_employee(
        self,
        selected_assignments: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        employee_hours: dict[str, float] = defaultdict(float)

        for assignment in selected_assignments:
            employee_name = assignment["employee_name"]
            duration = self._hours_between(
                assignment.get("start_time"),
                assignment.get("end_time"),
            )
            employee_hours[employee_name] += duration

        for employee_name, total_hours in employee_hours.items():
            if total_hours > 40:
                errors.append(
                    {
                        "type": "max_hours_violation",
                        "employee_name": employee_name,
                        "assigned_hours": total_hours,
                        "max_hours": 40,
                        "message": (
                            f"{employee_name} exceeds weekly hour limit: "
                            f"{total_hours} > 40."
                        ),
                    }
                )

        return errors

    def _check_max_shifts_per_employee(
        self,
        selected_assignments: list[dict[str, Any]],
        employee_lookup: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        employee_shift_counts: dict[str, int] = defaultdict(int)

        for assignment in selected_assignments:
            employee_shift_counts[assignment["employee_name"]] += 1

        for employee_name, assigned_count in employee_shift_counts.items():
            employee = employee_lookup.get(employee_name, {})
            max_shifts = employee.get("max_shifts_per_week")
            if max_shifts is not None and assigned_count > max_shifts:
                errors.append(
                    {
                        "type": "max_shifts_violation",
                        "employee_name": employee_name,
                        "assigned_shifts": assigned_count,
                        "max_shifts": max_shifts,
                        "message": (
                            f"{employee_name} exceeds weekly shift limit: "
                            f"{assigned_count} > {max_shifts}."
                        ),
                    }
                )

        return errors

    def _check_cannot_work_with_pairs(
        self,
        selected_assignments: list[dict[str, Any]],
        employee_lookup: dict[str, dict[str, Any]],
        constraints: dict[str, Any],
    ) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []

        pair_exclusions = self._cannot_work_with_pairs(employee_lookup, constraints)
        exclusion_set = {
            tuple(sorted(pair))
            for pair in pair_exclusions
            if isinstance(pair, list) and len(pair) == 2
        }

        grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for assignment in selected_assignments:
            key = (
                assignment.get("day", ""),
                assignment.get("start_time", ""),
                assignment.get("end_time", ""),
                assignment.get("location", "") or "",
            )
            grouped[key].append(assignment)

        for assignments in grouped.values():
            employee_names = [assignment["employee_name"] for assignment in assignments]

            for index, employee_a in enumerate(employee_names):
                for employee_b in employee_names[index + 1 :]:
                    pair = tuple(sorted([employee_a, employee_b]))
                    if pair in exclusion_set:
                        errors.append(
                            {
                                "type": "cannot_work_with_violation",
                                "employees": list(pair),
                                "message": (
                                    f"{pair[0]} and {pair[1]} are assigned together "
                                    "but cannot work together."
                                ),
                            }
                        )

        return errors

    def _cannot_work_with_pairs(
        self,
        employee_lookup: dict[str, dict[str, Any]],
        constraints: dict[str, Any],
    ) -> list[list[str]]:
        pairs = list(constraints.get("cannot_work_with_pairs", []))
        for employee_name, employee in employee_lookup.items():
            for blocked_name in employee.get("cannot_work_with", []):
                pairs.append([employee_name, blocked_name])
        return pairs

    def _matches_availability(
        self,
        employee: dict[str, Any],
        shift: dict[str, Any],
    ) -> bool:
        availability = set(employee.get("availability", []))
        if not availability:
            return True

        day = shift.get("day", "")
        time = shift.get("time", "")
        shift_label = shift.get("shift_label", "")
        candidates = {day, f"{day}_{time}", f"{day}_{shift_label}"}

        return bool(availability.intersection(candidate for candidate in candidates if candidate))

    def _same_day(self, day_a: str | None, day_b: str | None) -> bool:
        return (day_a or "").strip().lower() == (day_b or "").strip().lower()

    def _times_overlap(
        self,
        start_a: str | None,
        end_a: str | None,
        start_b: str | None,
        end_b: str | None,
    ) -> bool:
        if not all([start_a, end_a, start_b, end_b]):
            return False

        range_a = self._time_range_to_minutes(start_a, end_a)
        range_b = self._time_range_to_minutes(start_b, end_b)

        return any(
            max(a_start, b_start) < min(a_end, b_end)
            for a_start, a_end in range_a
            for b_start, b_end in range_b
        )

    def _hours_between(self, start_time: str | None, end_time: str | None) -> float:
        if not start_time or not end_time:
            return 0.0

        ranges = self._time_range_to_minutes(start_time, end_time)
        return sum((end - start) / 60.0 for start, end in ranges)

    def _time_range_to_minutes(
        self,
        start_time: str,
        end_time: str,
    ) -> list[tuple[int, int]]:
        start_minutes = self._clock_to_minutes(start_time)
        end_minutes = self._clock_to_minutes(end_time)

        if start_minutes < end_minutes:
            return [(start_minutes, end_minutes)]

        return [(start_minutes, 24 * 60), (0, end_minutes)]

    def _clock_to_minutes(self, value: str) -> int:
        hours, minutes = value.split(":", maxsplit=1)
        return int(hours) * 60 + int(minutes)
