from arq import create_pool
from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_operator
from ..config import arq_redis_settings
from ..db import db, now, oid, serialize
from ..events import emit
from ..schemas import AiActionDecision
from ..services.incidents import audit, invalidate_incident, mutate_incident, write_activity

router = APIRouter(tags=["ai"])


@router.post("/incidents/{incident_id}/ai-investigation")
async def start_investigation(incident_id: str, user: dict = Depends(require_operator)):
    existing = await db().ai_runs.find_one({"incident_id": oid(incident_id), "status": {"$in": ["queued", "running"]}})
    if existing:
        return serialize(existing)
    doc = {"incident_id": oid(incident_id), "status": "queued", "idempotency_key": f"incident:{incident_id}", "created_at": now(), "updated_at": now()}
    result = await db().ai_runs.insert_one(doc)
    doc["_id"] = result.inserted_id
    try:
        pool = await create_pool(arq_redis_settings())
        await pool.enqueue_job("investigate_incident", incident_id, str(result.inserted_id), user["_id"])
        await pool.aclose()
    except Exception:
        await db().ai_runs.update_one({"_id": result.inserted_id}, {"$set": {"status": "failed", "error": "Queue unavailable", "updated_at": now()}})
    await emit("ai.state_changed", serialize(doc), f"incident:{incident_id}")
    return serialize(doc)


async def _execute_action(action: dict, user: dict) -> dict:
    incident_id = str(action["incident_id"])
    tool = action["tool"]
    args = action["args"]
    if tool == "change_severity":
        await mutate_incident(incident_id, {"severity": args["severity"]}, user)
    elif tool == "assign_incident":
        await mutate_incident(incident_id, {"assignee_id": args["assignee_id"]}, user)
    else:
        raise HTTPException(400, "Unsupported approval action")
    await db().ai_actions.update_one({"_id": action["_id"]}, {"$set": {"status": "executed", "decided_at": now(), "decided_by": oid(user["_id"])}})
    await write_activity(incident_id, user["_id"], "ai.action_executed", f"Approved {tool}", args)
    await audit(user["_id"], "ai.action_executed", "incident", incident_id, {"tool": tool, "args": args})
    await invalidate_incident(incident_id)
    executed = await db().ai_actions.find_one({"_id": action["_id"]})
    await emit("ai.action_executed", serialize(executed), f"incident:{incident_id}")
    return executed


@router.post("/ai-actions/{action_id}/approve")
async def approve_action(action_id: str, payload: AiActionDecision, user: dict = Depends(require_operator)):
    action = await db().ai_actions.find_one({"_id": oid(action_id), "status": "pending"})
    if not action:
        raise HTTPException(404, "Pending action not found")
    return serialize(await _execute_action(action, user))


@router.post("/ai-actions/{action_id}/reject")
async def reject_action(action_id: str, payload: AiActionDecision, user: dict = Depends(require_operator)):
    action = await db().ai_actions.find_one({"_id": oid(action_id), "status": "pending"})
    if not action:
        raise HTTPException(404, "Pending action not found")
    await db().ai_actions.update_one({"_id": action["_id"]}, {"$set": {"status": "rejected", "decision_note": payload.note, "decided_at": now(), "decided_by": oid(user["_id"])}})
    await write_activity(action["incident_id"], user["_id"], "ai.action_rejected", f"Rejected {action['tool']}")
    await audit(user["_id"], "ai.action_rejected", "incident", action["incident_id"], {"tool": action["tool"]})
    await invalidate_incident(action["incident_id"])
    rejected = await db().ai_actions.find_one({"_id": action["_id"]})
    await emit("ai.action_pending", serialize(rejected), f"incident:{action['incident_id']}")
    return serialize(rejected)
