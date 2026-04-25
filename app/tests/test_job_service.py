from app.services.job_service import JobNotFoundError, JobService


class FakeCollection:
    def __init__(self) -> None:
        self.documents = {}

    def insert_one(self, document: dict) -> None:
        self.documents[document["job_id"]] = document

    def find_one(self, query: dict, projection: dict) -> dict | None:
        document = self.documents.get(query["job_id"])
        if document is None:
            return None

        if projection.get("_id") == 0:
            return {key: value for key, value in document.items() if key != "_id"}

        return document


def test_create_and_get_job(monkeypatch) -> None:
    fake_collection = FakeCollection()

    monkeypatch.setattr(JobService, "__init__", lambda self: setattr(self, "collection", fake_collection))

    service = JobService()
    job_id = service.create_job({"status": "success", "is_valid": True})
    job = service.get_job(job_id)

    assert job["job_id"] == job_id
    assert job["status"] == "success"
    assert job["is_valid"] is True
    assert "created_at" in job


def test_create_job_converts_keys_for_mongo(monkeypatch) -> None:
    fake_collection = FakeCollection()

    monkeypatch.setattr(JobService, "__init__", lambda self: setattr(self, "collection", fake_collection))

    service = JobService()
    job_id = service.create_job({"color_to_time_slot": {0: {"assignments": ("a", "b")}}})
    job = service.get_job(job_id)

    assert job["color_to_time_slot"] == {"0": {"assignments": ["a", "b"]}}


def test_missing_job_raises(monkeypatch) -> None:
    fake_collection = FakeCollection()

    monkeypatch.setattr(JobService, "__init__", lambda self: setattr(self, "collection", fake_collection))

    service = JobService()

    try:
        service.get_job("missing")
    except JobNotFoundError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("Expected JobNotFoundError")
