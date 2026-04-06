

class NormalizationService:
    def normalize(self, data: dict[str, str]) -> dict[str, str]:
        return {key: value.strip().lower() for key, value in data.items()}
