from __future__ import annotations

import re
from typing import Any

from app.models.extraction import ExtractedConstraints


class NormalizationError(Exception):
    pass


class NormalizationService:
    VALID_DAYS = {
        "mon": "monday",
        "monday": "monday",
        "tue": "tuesday",
        "tues": "tuesday",
        "tuesday": "tuesday",
        "wed": "wednesday",
        "weds": "wednesday",
        "wednesday": "wednesday",
        "thu": "thursday",
        "thur": "thursday",
        "thurs": "thursday",
        "thursday": "thursday",
        "fri": "friday",
        "friday": "friday",
        "sat": "saturday",
        "saturday": "saturday",
        "sun": "sunday",
        "sunday": "sunday",
    }

    VALID_TIMES = {
        "morning": "morning",
        "am": "morning",
        "day": "morning",
        "afternoon": "afternoon",
        "pm": "afternoon",
        "evening": "evening",
        "night": "night",
        "overnight": "night",
    }

    def normalize(self, extracted: ExtractedConstraints) -> dict[str, Any]:
        data = extracted.model_dump()

        data["entities"]["employees"] = self._normalize_employees(
            data["entities"].get("employees", [])
        )
        data["entities"]["shifts"] = self._normalize_shifts(
            data["entities"].get("shifts", [])
        )
        data["constraints"] = self._normalize_constraints(
            data.get("constraints", {})
        )

        self._validate_consistency(data)

        return data

    def _normalize_employees(self, employees: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}

        for employee in employees:
            name = self._normalize_person_name(employee.get("name"))
            if not name:
                continue

            skills = self._dedupe_list(
                [self._normalize_skill(s) for s in employee.get("skills", []) if s]
            )

            availability = self._dedupe_list(
                [self._normalize_availability(a) for a in employee.get("availability", []) if a]
            )

            cannot_work_with = self._dedupe_list(
                [self._normalize_person_name(n) for n in employee.get("cannot_work_with", []) if n]
            )

            max_shifts = employee.get("max_shifts_per_week")
            if max_shifts is not None:
                try:
                    max_shifts = int(max_shifts)
                except (TypeError, ValueError):
                    max_shifts = None

            normalized = {
                "name": name,
                "skills": skills,
                "availability": availability,
                "max_shifts_per_week": max_shifts,
                "cannot_work_with": cannot_work_with,
            }

            key = name.lower()
            if key not in merged:
                merged[key] = normalized
            else:
                merged[key]["skills"] = self._dedupe_list(merged[key]["skills"] + skills)
                merged[key]["availability"] = self._dedupe_list(
                    merged[key]["availability"] + availability
                )
                merged[key]["cannot_work_with"] = self._dedupe_list(
                    merged[key]["cannot_work_with"] + cannot_work_with
                )

                old_max = merged[key]["max_shifts_per_week"]
                if old_max is None:
                    merged[key]["max_shifts_per_week"] = max_shifts
                elif max_shifts is not None:
                    merged[key]["max_shifts_per_week"] = min(old_max, max_shifts)

        return list(merged.values())

    def _normalize_shifts(self, shifts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: dict[tuple[str, str, str], dict[str, Any]] = {}
        generated_id_counter = 1

        for shift in shifts:
            day = self._normalize_day(shift.get("day"))
            time = self._normalize_time(shift.get("time"))
            location = self._normalize_text(shift.get("location"))

            required_skills = self._dedupe_list(
                [self._normalize_skill(s) for s in shift.get("required_skills", []) if s]
            )

            min_staff = self._safe_int(shift.get("min_staff"), default=1)
            max_staff = self._safe_int(shift.get("max_staff"), default=1)

            shift_id = self._normalize_text(shift.get("id"))
            if not shift_id:
                shift_id = f"shift_{generated_id_counter}"
                generated_id_counter += 1

            key = (day, time, location or "")

            normalized = {
                "id": shift_id,
                "day": day,
                "time": time,
                "location": location,
                "required_skills": required_skills,
                "min_staff": min_staff,
                "max_staff": max_staff,
            }

            if key not in merged:
                merged[key] = normalized
            else:
                merged[key]["required_skills"] = self._dedupe_list(
                    merged[key]["required_skills"] + required_skills
                )
                merged[key]["min_staff"] = max(merged[key]["min_staff"], min_staff)
                merged[key]["max_staff"] = max(merged[key]["max_staff"], max_staff)

        return list(merged.values())

    def _normalize_constraints(self, constraints: dict[str, Any]) -> dict[str, list[str]]:
        hard = self._dedupe_list(
            [self._normalize_constraint(c) for c in constraints.get("hard_constraints", []) if c]
        )
        soft = self._dedupe_list(
            [self._normalize_constraint(c) for c in constraints.get("soft_constraints", []) if c]
        )

        return {
            "hard_constraints": hard,
            "soft_constraints": soft,
        }

    def _validate_consistency(self, data: dict[str, Any]) -> None:
        employees = data["entities"]["employees"]
        shifts = data["entities"]["shifts"]

        valid_availability_labels = {"morning", "afternoon", "evening", "night"}

        employee_names = {e["name"] for e in employees}

        for employee in employees:
            if not employee["name"]:
                raise NormalizationError("Employee name cannot be empty.")

            for person in employee["cannot_work_with"]:
                if person == employee["name"]:
                    raise NormalizationError(
                        f'Employee "{employee["name"]}" cannot list themselves in cannot_work_with.'
                    )

            for slot in employee["availability"]:
                # expected format like monday_morning
                parts = slot.split("_")
                if len(parts) < 2:
                    raise NormalizationError(
                        f'Invalid availability format "{slot}" for employee "{employee["name"]}".'
                    )
                day = parts[0]
                shift = "_".join(parts[1:])
                if day not in set(self.VALID_DAYS.values()):
                    raise NormalizationError(
                        f'Invalid day "{day}" in availability "{slot}" for employee "{employee["name"]}".'
                    )
                if shift not in valid_availability_labels:
                    raise NormalizationError(
                        f'Invalid shift "{shift}" in availability "{slot}" for employee "{employee["name"]}".'
                    )

        seen_shift_ids: set[str] = set()
        for shift in shifts:
            if not shift["id"]:
                raise NormalizationError("Shift id cannot be empty.")
            if shift["id"] in seen_shift_ids:
                raise NormalizationError(f'Duplicate shift id found: "{shift["id"]}".')
            seen_shift_ids.add(shift["id"])

            if shift["day"] not in set(self.VALID_DAYS.values()):
                raise NormalizationError(f'Invalid shift day "{shift["day"]}".')
            if shift["time"] not in set(self.VALID_TIMES.values()):
                raise NormalizationError(f'Invalid shift time "{shift["time"]}".')
            if shift["min_staff"] < 1:
                raise NormalizationError(f'Shift "{shift["id"]}" min_staff must be at least 1.')
            if shift["max_staff"] < shift["min_staff"]:
                raise NormalizationError(
                    f'Shift "{shift["id"]}" has max_staff < min_staff.'
                )

        for employee in employees:
            for person in employee["cannot_work_with"]:
                if person not in employee_names:
                    # not fatal, but strict validation helps
                    raise NormalizationError(
                        f'Employee "{employee["name"]}" references unknown person "{person}" in cannot_work_with.'
                    )

    def _normalize_day(self, value: Any) -> str:
        text = self._normalize_text(value)
        if not text:
            return ""
        return self.VALID_DAYS.get(text, text)

    def _normalize_time(self, value: Any) -> str:
        text = self._normalize_text(value)
        if not text:
            return ""
        return self.VALID_TIMES.get(text, text)

    def _normalize_skill(self, value: Any) -> str:
        text = self._normalize_text(value)
        if not text:
            return ""
        return re.sub(r"\s+", "_", text)

    def _normalize_constraint(self, value: Any) -> str:
        text = self._normalize_text(value)
        if not text:
            return ""
        return re.sub(r"\s+", "_", text)

    def _normalize_person_name(self, value: Any) -> str:
        text = self._normalize_text(value)
        if not text:
            return ""
        return " ".join(part.capitalize() for part in text.split())

    def _normalize_availability(self, value: Any) -> str:
        text = self._normalize_text(value)
        if not text:
            return ""

        text = text.replace("-", " ").replace("_", " ")
        parts = text.split()

        if len(parts) >= 2:
            day = self._normalize_day(parts[0])
            time = self._normalize_time(parts[1])
            return f"{day}_{time}"

        return text

    def _normalize_text(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip().lower()

    def _safe_int(self, value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _dedupe_list(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []

        for item in items:
            if item and item not in seen:
                seen.add(item)
                result.append(item)

        return result