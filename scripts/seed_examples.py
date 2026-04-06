from pathlib import Path


def main() -> None:
    sample = {"example": "This is a placeholder for seeded schedule examples."}
    path = Path(__file__).resolve().parent / "examples.json"
    path.write_text(str(sample))


if __name__ == "__main__":
    main()
