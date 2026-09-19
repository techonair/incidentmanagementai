import json
from typing import Any

from redis.asyncio import Redis

from .config import settings
from .db import serialize

redis: Redis | None = None


async def connect_cache() -> None:
    global redis
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await redis.ping()
    except Exception:
        redis = None


async def close_cache() -> None:
    if redis:
        await redis.aclose()


async def get_json(key: str) -> Any | None:
    if not redis:
        return None
    try:
        raw = await redis.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


async def set_json(key: str, value: Any, ttl: int) -> None:
    if not redis:
        return
    try:
        await redis.set(key, json.dumps(serialize(value)), ex=ttl)
    except Exception:
        return


async def delete_keys(*keys: str) -> None:
    if not redis or not keys:
        return
    try:
        await redis.delete(*keys)
    except Exception:
        return


async def publish(channel: str, event: dict[str, Any]) -> None:
    if not redis:
        return
    try:
        await redis.publish(channel, json.dumps(serialize(event)))
    except Exception:
        return
