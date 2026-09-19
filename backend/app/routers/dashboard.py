from datetime import timedelta

from fastapi import APIRouter, Depends

from ..auth import require_operator
from ..cache import get_json, set_json
from ..db import db, now, serialize

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
async def overview(user: dict = Depends(require_operator)):
    cached = await get_json("dash:overview")
    if cached:
        return cached
    open_count = await db().incidents.count_documents({"status": {"$ne": "resolved"}})
    sev12 = await db().incidents.count_documents({"severity": {"$in": ["sev1", "sev2"]}, "status": {"$ne": "resolved"}})
    aging = await db().incidents.count_documents({"status": {"$ne": "resolved"}, "created_at": {"$lte": now() - timedelta(hours=24)}})
    by_status = await db().incidents.aggregate([{"$group": {"_id": "$status", "count": {"$sum": 1}}}]).to_list(20)
    by_severity = await db().incidents.aggregate([{"$group": {"_id": "$severity", "count": {"$sum": 1}}}]).to_list(20)
    by_team = await db().incidents.aggregate([{"$group": {"_id": "$team_id", "count": {"$sum": 1}}}]).to_list(20)
    recent = await db().activities.find({}).sort("created_at", -1).limit(10).to_list(10)
    payload = serialize({"open": open_count, "sev1_2": sev12, "aging": aging, "by_status": by_status, "by_severity": by_severity, "by_team": by_team, "recent_activity": recent})
    await set_json("dash:overview", payload, 15)
    return payload
