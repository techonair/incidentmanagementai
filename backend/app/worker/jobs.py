from ..cache import close_cache, connect_cache
from ..db import connect, db, now, oid, serialize
from ..events import emit
from ..services.ai import deterministic_investigation
from ..services.incidents import audit, invalidate_incident, write_activity


async def startup(ctx):
    await connect()
    await connect_cache()


async def shutdown(ctx):
    from ..db import close
    await close_cache()
    await close()


async def correlate_alert(ctx, incident_id: str):
    await write_activity(incident_id, None, "alert.correlated", "Alert correlation completed")
    await emit("incident.updated", {"_id": incident_id}, f"incident:{incident_id}")


async def investigate_incident(ctx, incident_id: str, run_id: str, actor_id: str):
    database = db()
    run_oid = oid(run_id)
    await database.ai_runs.update_one({"_id": run_oid}, {"$set": {"status": "running", "updated_at": now()}})
    await emit("ai.state_changed", {"_id": run_id, "status": "running"}, f"incident:{incident_id}")
    try:
        incident = await database.incidents.find_one({"_id": oid(incident_id)})
        alerts = await database.alerts.find({"incident_id": oid(incident_id)}).sort("created_at", -1).limit(20).to_list(20)
        keywords = " ".join(incident["title"].split()[:3])
        similar = await database.incidents.find({
            "_id": {"$ne": oid(incident_id)},
            "service": incident["service"],
            "severity": incident["severity"],
            "$text": {"$search": keywords},
        }).limit(5).to_list(5)
        workload = await database.incidents.aggregate([
            {"$match": {"status": {"$ne": "resolved"}}},
            {"$group": {"_id": "$team_id", "count": {"$sum": 1}}},
        ]).to_list(100)
        output = await deterministic_investigation(incident, alerts, similar, workload)
        await database.ai_runs.update_one({"_id": run_oid}, {"$set": {"status": "completed", "output": output, "updated_at": now()}})
        for action in output["recommended_actions"]:
            if action["tool"] == "add_note":
                await write_activity(incident_id, actor_id, "ai.note", action["args"]["body"])
            elif action["tool"] == "create_task":
                task = {"incident_id": oid(incident_id), "title": action["args"]["title"], "status": "todo", "created_at": now(), "updated_at": now()}
                await database.tasks.insert_one(task)
                await write_activity(incident_id, actor_id, "task.created", action["args"]["title"], {"source": "ai"})
            elif action["requires_approval"]:
                pending = {
                    "incident_id": oid(incident_id),
                    "ai_run_id": run_oid,
                    "tool": action["tool"],
                    "args": action["args"],
                    "status": "pending",
                    "created_at": now(),
                }
                result = await database.ai_actions.insert_one(pending)
                pending["_id"] = result.inserted_id
                await emit("ai.action_pending", serialize(pending), f"incident:{incident_id}")
        await audit(actor_id, "ai.investigation.completed", "incident", incident_id, {"run_id": run_id})
        await invalidate_incident(incident_id)
        await emit("ai.state_changed", {"_id": run_id, "status": "completed", "output": output}, f"incident:{incident_id}")
    except Exception as exc:
        await database.ai_runs.update_one({"_id": run_oid}, {"$set": {"status": "failed", "error": str(exc), "updated_at": now()}})
        await emit("ai.state_changed", {"_id": run_id, "status": "failed", "error": str(exc)}, f"incident:{incident_id}")
