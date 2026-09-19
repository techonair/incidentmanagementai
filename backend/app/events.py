import asyncio
import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

from . import cache
from .cache import publish
from .db import serialize

connections: dict[str, set[WebSocket]] = defaultdict(set)


async def emit(event: str, payload: dict[str, Any], room: str = "global") -> None:
    message = {"event": event, "room": room, "payload": serialize(payload)}
    await publish("events", message)
    await broadcast(message)


async def broadcast(message: dict[str, Any]) -> None:
    rooms = {"global", message.get("room", "global")}
    dead: list[tuple[str, WebSocket]] = []
    for room in rooms:
        for ws in list(connections.get(room, set())):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append((room, ws))
    for room, ws in dead:
        connections[room].discard(ws)


async def subscribe(ws: WebSocket, rooms: list[str]) -> None:
    await ws.accept()
    selected = set(rooms or ["global"]) | {"global"}
    for room in selected:
        connections[room].add(ws)
    try:
        while True:
            data = await ws.receive_json()
            if data.get("type") == "join":
                room = data.get("room")
                if room:
                    connections[room].add(ws)
    finally:
        for room in list(connections.keys()):
            connections[room].discard(ws)


async def redis_event_listener() -> None:
    if not cache.redis:
        return
    pubsub = cache.redis.pubsub()
    await pubsub.subscribe("events")
    async for item in pubsub.listen():
        if item["type"] == "message":
            await broadcast(json.loads(item["data"]))


def start_listener() -> None:
    if cache.redis:
        asyncio.create_task(redis_event_listener())
