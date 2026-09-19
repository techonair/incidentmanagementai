from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import settings

client: AsyncIOMotorClient | None = None


def now() -> datetime:
    return datetime.now(UTC)


def oid(value: str | ObjectId) -> ObjectId:
    if isinstance(value, ObjectId):
        return value
    return ObjectId(value)


def serialize(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [serialize(v) for v in value]
    if isinstance(value, dict):
        return {k: serialize(v) for k, v in value.items()}
    return value


async def connect() -> None:
    global client
    client = AsyncIOMotorClient(settings.mongo_url)


async def close() -> None:
    if client:
        client.close()


def db() -> AsyncIOMotorDatabase:
    if client is None:
        raise RuntimeError("database not connected")
    return client[settings.mongo_db]


async def ensure_indexes(database: AsyncIOMotorDatabase) -> None:
    await database.incidents.create_index(
        [
            ("status", 1),
            ("severity", 1),
            ("team_id", 1),
            ("assignee_id", 1),
            ("updated_at", -1),
        ]
    )
    await database.incidents.create_index([("title", "text"), ("summary", "text")])
    await database.alerts.create_index([("fingerprint", 1), ("created_at", -1)])
    for name in ("activities", "comments", "tasks"):
        await database[name].create_index([("incident_id", 1), ("created_at", -1)])
