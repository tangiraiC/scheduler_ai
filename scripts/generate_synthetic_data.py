from pathlib import Path


def main() -> None:
    path = Path(__file__).resolve().parent / "synthetic_data.json"
    data = [{"task": "Example task", "duration": 60}]
    path.write_text(str(data))


if __name__ == "__main__":
    main()
