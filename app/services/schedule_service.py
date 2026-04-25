from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.models.extraction import ExtractedConstraints
from app.services.extraction_service import ExtractionService, ExtractionServiceError
from app.services.graph_service import GraphConstructionError, GraphService
from app.services.normalization_service import NormalizationError, NormalizationService
from app.services.solver_service import SolverService, SolverServiceError
from app.services.validation_service import ValidationService, ValidationServiceError


class ScheduleServiceError(Exception):
    pass


class ScheduleService:
    """
    Full pipeline orchestration service.

    Pipeline:
    1. Extract constraints from raw text
    2. Normalize extracted structure
    3. Build and solve the conflict graph
    4. Validate final schedule
    5. Return unified response
    """

    def __init__(self) -> None:
        self.extraction_service = ExtractionService()
        self.normalization_service = NormalizationService()
        self.graph_service = GraphService()
        self.solver_service = SolverService()
        self.validation_service = ValidationService()

    async def run(
        self,
        raw_text: str,
        strategy: str = "largest_first",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not raw_text or not raw_text.strip():
            raise ScheduleServiceError("raw_text is required.")

        metadata = metadata or {}
        stage_trace: list[dict[str, Any]] = []

        try:
            stage_trace.append({"stage": "extraction", "status": "started"})
            extraction_result = await self.extraction_service.extract(raw_text)
            extracted_data = self._extract_data_payload(extraction_result)
            stage_trace[-1]["status"] = "completed"

            return self._run_from_extracted_data(
                extracted_data=extracted_data,
                strategy=strategy,
                metadata=metadata,
                stage_trace=stage_trace,
                raw_text=raw_text,
            )
        except Exception as exc:
            self._mark_failed_stage(stage_trace, exc)
            raise self._pipeline_error(stage_trace, exc) from exc

    def run_from_constraints(
        self,
        constraints: dict[str, Any],
        strategy: str = "largest_first",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata = metadata or {}
        stage_trace: list[dict[str, Any]] = []

        try:
            return self._run_from_extracted_data(
                extracted_data=constraints,
                strategy=strategy,
                metadata=metadata,
                stage_trace=stage_trace,
                raw_text=None,
            )
        except Exception as exc:
            self._mark_failed_stage(stage_trace, exc)
            raise self._pipeline_error(stage_trace, exc) from exc

    def build_schedule(
        self,
        constraints: dict[str, Any],
        strategy: str = "largest_first",
    ) -> dict[str, Any]:
        """
        Backward-compatible entry point for existing structured callers.
        """
        return self.run_from_constraints(constraints=constraints, strategy=strategy)

    def _run_from_extracted_data(
        self,
        extracted_data: dict[str, Any],
        strategy: str,
        metadata: dict[str, Any],
        stage_trace: list[dict[str, Any]],
        raw_text: str | None,
    ) -> dict[str, Any]:
        stage_trace.append({"stage": "normalization", "status": "started"})
        extracted_data = self._coerce_extracted_data(extracted_data)
        extracted_model = ExtractedConstraints.model_validate(extracted_data)
        normalized_data = self.normalization_service.normalize(extracted_model)
        stage_trace[-1]["status"] = "completed"

        stage_trace.append({"stage": "graph_construction", "status": "started"})
        graph_summary = self._build_graph_summary(normalized_data)
        stage_trace[-1]["status"] = "completed"

        stage_trace.append({"stage": "solving", "status": "started"})
        schedule_result = self.solver_service.solve(
            normalized_data=normalized_data,
            strategy=strategy,
        )
        stage_trace[-1]["status"] = "completed"

        stage_trace.append({"stage": "validation", "status": "started"})
        validation_result = self.validation_service.validate(
            normalized_data=normalized_data,
            schedule_result=schedule_result,
        )
        stage_trace[-1]["status"] = "completed"

        return {
            "status": "success",
            "stage_trace": stage_trace,
            "input": {
                "raw_text": raw_text,
                "strategy": strategy,
                "metadata": metadata,
            },
            "extracted_data": extracted_data,
            "normalized_data": normalized_data,
            "graph_summary": {
                **graph_summary,
                "color_count": schedule_result.get("color_count", 0),
            },
            "schedule_result": schedule_result,
            "validation": validation_result,
            "final_schedule": schedule_result.get("schedule", {}),
            "is_valid": validation_result.get("is_valid", False),
            "nodes": schedule_result.get("nodes", []),
            "edges": schedule_result.get("edges", []),
        }

    def _build_graph_summary(self, normalized_data: dict[str, Any]) -> dict[str, int]:
        graph_result = self.graph_service.build_conflict_graph(normalized_data)
        return {
            "node_count": graph_result.get("node_count", 0),
            "edge_count": graph_result.get("edge_count", 0),
        }

    def _extract_data_payload(self, extraction_result: Any) -> dict[str, Any]:
        if isinstance(extraction_result, ExtractedConstraints):
            return extraction_result.model_dump()

        if not isinstance(extraction_result, dict):
            raise ScheduleServiceError("Extraction result must be a dictionary.")

        data = extraction_result.get("data", extraction_result)
        if not isinstance(data, dict):
            raise ScheduleServiceError("Extraction result data must be a dictionary.")

        return data

    def _coerce_extracted_data(self, extracted_data: dict[str, Any]) -> dict[str, Any]:
        data = {
            **extracted_data,
            "entities": {
                **extracted_data.get("entities", {}),
                "shifts": [
                    self._coerce_shift_data(shift)
                    for shift in extracted_data.get("entities", {}).get("shifts", [])
                ],
            },
        }
        return data

    def _coerce_shift_data(self, shift: dict[str, Any]) -> dict[str, Any]:
        if shift.get("time"):
            return shift

        start_time = shift.get("start_time")
        end_time = shift.get("end_time")
        if start_time and end_time:
            return {
                **shift,
                "time": f"{start_time}-{end_time}",
            }

        return shift

    def _mark_failed_stage(
        self,
        stage_trace: list[dict[str, Any]],
        exc: Exception,
    ) -> None:
        if stage_trace:
            stage_trace[-1]["status"] = "failed"
            stage_trace[-1]["error"] = str(exc)

    def _pipeline_error(
        self,
        stage_trace: list[dict[str, Any]],
        exc: Exception,
    ) -> ScheduleServiceError:
        expected_errors = (
            ExtractionServiceError,
            NormalizationError,
            GraphConstructionError,
            SolverServiceError,
            ValidationServiceError,
            ScheduleServiceError,
            ValidationError,
            ValueError,
            KeyError,
            TypeError,
        )
        message = str(exc) if isinstance(exc, expected_errors) else f"Unexpected schedule pipeline failure: {exc}"
        return ScheduleServiceError(
            {
                "message": "Schedule pipeline failed",
                "stage_trace": stage_trace,
                "error": message,
            }
        )
