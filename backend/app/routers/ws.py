from fastapi import APIRouter, WebSocket

from ..events import subscribe

router = APIRouter(tags=["ws"])


@router.websocket("/ws")
async def websocket(ws: WebSocket):
    rooms = ws.query_params.get("rooms", "global").split(",")
    await subscribe(ws, rooms)
