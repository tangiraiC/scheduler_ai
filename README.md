# Scheduler AI

A lightweight scheduler API boilerplate with FastAPI, SQLAlchemy, and modular service layers.

## Quickstart

1. Create and activate the virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. Open http://localhost:8000/api/v1/health

## Docker Compose

Run with:
```bash
docker compose up
```
