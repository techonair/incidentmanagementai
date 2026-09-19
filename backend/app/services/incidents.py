from datetime import timedelta
from typing import Any

from fastapi import HTTPException

from ..cache import delete_keys
from ..db import db, now, oid, serialize
from ..events import emit


async def write_activity(incident_id, actor_id, kind: str, message: str, meta: dict[str, Any] | None = None) -> None:
    doc = {
        "incident_id": oid(incident_id),
        "actor_id": oid(actor_id) if actor_id else None,
        "kind": kind,
        "message": message,
        "meta": meta or {},
        "created_at": now(),
    }
    await db().activities.insert_one(doc)


async def audit(actor_id, action: str, target_type: str, target_id, meta: dict[str, Any] | None = None) -> None:
    await db().audit_log.insert_one({
        "actor_id": oid(actor_id) if actor_id else None,
        "action": action,
        "target_type": target_type,
        "target_id": oid(target_id),
        "meta": meta or {},
        "created_at": now(),
    })


async def invalidate_incident(incident: dict | str) -> None:
    incident_id = str(incident["_id"] if isinstance(incident, dict) else incident)
    await delete_keys(f"incident:{incident_id}", "dash:overview", "team:workload")


async def get_incident_or_404(incident_id: str) -> dict:
    incident = await db().incidents.find_one({"_id": oid(incident_id)})
    if not incident:
        raise HTTPException(404, "Incident not found")
    return incident


async def mutate_incident(incident_id: str, patch: dict[str, Any], actor: dict) -> dict:
    incident = await get_incident_or_404(incident_id)
    if incident["status"] == "resolved" and patch.get("status") != "open" and actor["role"] != "admin":
        raise HTTPException(403, "Resolved incidents are locked")
    if patch.get("severity") == "sev1" and actor["role"] != "admin":
        raise HTTPException(403, "Only admins may assign sev1")
    update = {k: v for k, v in patch.items() if v is not None}
    if not update:
        return incident
    update["updated_at"] = now()
    for key in ("team_id", "assignee_id"):
        if key in update and update[key]:
            update[key] = oid(update[key])
    await db().incidents.update_one({"_id": incident["_id"]}, {"$set": update})
    changed = await get_incident_or_404(incident_id)
    await write_activity(incident_id, actor["_id"], "incident.updated", "Incident updated", update)
    await audit(actor["_id"], "incident.updated", "incident", incident_id, update)
    await invalidate_incident(changed)
    await emit("incident.updated", serialize(changed), f"incident:{incident_id}")
    return changed


async def create_incident(doc: dict[str, Any], actor_id=None) -> dict:
    stamp = now()
    payload = {**doc, "status": doc.get("status", "open"), "created_at": stamp, "updated_at": stamp}
    for key in ("team_id", "assignee_id"):
        if payload.get(key):
            payload[key] = oid(payload[key])
    result = await db().incidents.insert_one(payload)
    incident = await get_incident_or_404(str(result.inserted_id))
    await write_activity(result.inserted_id, actor_id, "incident.created", "Incident created")
    await audit(actor_id, "incident.created", "incident", result.inserted_id)
    await invalidate_incident(incident)
    await emit("incident.created", serialize(incident), f"incident:{result.inserted_id}")
    return incident


async def link_or_create_alert(alert: dict[str, Any], actor_id=None) -> tuple[dict, bool]:
    window = now() - timedelta(minutes=30)
    existing_alert = await db().alerts.find_one({
        "fingerprint": alert["fingerprint"],
        "service": alert["service"],
        "created_at": {"$gte": window},
        "incident_id": {"$exists": True},
    })
    if existing_alert:
        incident_id = existing_alert["incident_id"]
        created = False
    else:
        incident = await create_incident({
            "title": alert["title"],
            "summary": alert.get("summary", ""),
            "service": alert["service"],
            "severity": alert.get("severity", "sev3"),
        }, actor_id)
        incident_id = incident["_id"]
        created = True
    alert_doc = {**alert, "incident_id": oid(incident_id), "created_at": now()}
    await db().alerts.insert_one(alert_doc)
    await write_activity(incident_id, actor_id, "alert.linked", f"Alert {alert['fingerprint']} linked")
    await audit(actor_id, "alert.linked", "incident", incident_id, {"fingerprint": alert["fingerprint"]})
    await emit("incident.updated", {"_id": str(incident_id)}, f"incident:{incident_id}")
    return await get_incident_or_404(str(incident_id)), created
