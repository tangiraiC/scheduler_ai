from __future__ import annotations

from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import settings


class MongoManager:
    client: MongoClient[dict[str, Any]] | None = None


mongo = MongoManager()


def connect_to_mongo() -> None:
    if mongo.client is None:
        mongo.client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=1000)


def close_mongo_connection() -> None:
    if mongo.client is not None:
        mongo.client.close()
        mongo.client = None


def get_database() -> Database[dict[str, Any]]:
    if mongo.client is None:
        connect_to_mongo()

    if mongo.client is None:
        raise RuntimeError("MongoDB client is not initialized.")

    return mongo.client[settings.mongo_db_name]


def ping_mongo() -> dict[str, Any]:
    database = get_database()
    database.command("ping")
    return {
        "database": settings.mongo_db_name,
        "uri": settings.mongo_uri,
    }
