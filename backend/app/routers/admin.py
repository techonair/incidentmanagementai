from fastapi import APIRouter, Depends

from ..auth import require_admin, require_operator
from ..cache import get_json, set_json
from ..db import db, serialize

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/refs")
async def refs(user: dict = Depends(require_operator)):
    cached = await get_json("ref:teams")
    if cached:
        return cached
    teams = await db().teams.find({}).sort("name", 1).to_list(100)
    users = await db().users.find({}, {"password_hash": 0}).sort("name", 1).to_list(100)
    payload = serialize({"teams": teams, "users": users})
    await set_json("ref:teams", payload, 300)
    return payload


@router.get("/workload")
async def workload(user: dict = Depends(require_operator)):
    cached = await get_json("team:workload")
    if cached:
        return cached
    rows = await db().incidents.aggregate([
        {"$match": {"status": {"$ne": "resolved"}}},
        {"$group": {"_id": "$team_id", "count": {"$sum": 1}}},
    ]).to_list(100)
    payload = serialize(rows)
    await set_json("team:workload", payload, 30)
    return payload
