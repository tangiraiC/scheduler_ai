from typing import Any


class GraphService:
    def build_graph(self, items: list[str]) -> dict[str, Any]:
        return {
            "nodes": [{"id": idx, "label": item} for idx, item in enumerate(items)],
            "edges": [],
        }
