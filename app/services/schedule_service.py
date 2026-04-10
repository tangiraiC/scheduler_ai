from typing import Any

from app.models.extraction import ExtractedConstraints
from app.services.graph_service import GraphService
from app.services.coloring_service import ColoringService
from app.services.normalization_service import NormalizationService


class ScheduleService:
    def __init__(self) -> None:
        self.graph_service = GraphService()
        self.coloring_service = ColoringService()
        self.normalizer = NormalizationService()

    def build_schedule(self, constraints: dict[str, Any]) -> dict[str, Any]:
        extracted = ExtractedConstraints.model_validate(constraints)
        normalized = self.normalizer.normalize(extracted)

        graph_items = []
        graph_items.extend(
            f'employee:{employee["name"]}' for employee in normalized["entities"]["employees"]
        )
        graph_items.extend(
            f'shift:{shift["id"]}:{shift["day"]}_{shift["time"]}'
            for shift in normalized["entities"]["shifts"]
        )
        graph_items.extend(
            f'hard_constraint:{constraint}'
            for constraint in normalized["constraints"]["hard_constraints"]
        )
        graph_items.extend(
            f'soft_constraint:{constraint}'
            for constraint in normalized["constraints"]["soft_constraints"]
        )

        graph = self.graph_service.build_graph(graph_items)
        return self.coloring_service.color_graph(graph)
