from app.services.graph_service import GraphService
from app.services.coloring_service import ColoringService
from app.services.normalization_service import NormalizationService


class ScheduleService:
    def __init__(self) -> None:
        self.graph_service = GraphService()
        self.coloring_service = ColoringService()
        self.normalizer = NormalizationService()

    def build_schedule(self, constraints: list[str]) -> dict[str, dict[str, str]]:
        normalized = self.normalizer.normalize({f"constraint_{i}": value for i, value in enumerate(constraints)})
        graph = self.graph_service.build_graph(list(normalized.values()))
        return self.coloring_service.color_graph(graph)
