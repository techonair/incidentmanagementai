from fastapi import APIRouter, Depends, Query

from ..auth import require_operator
from ..cache import get_json, set_json
from ..db import db, now, oid, serialize
from ..events import emit
from ..schemas import CommentIn, IncidentIn, IncidentPatch, TaskIn, TaskPatch
from ..services.incidents import audit, create_incident, get_incident_or_404, invalidate_incident, mutate_incident, write_activity

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("")
async def list_incidents(
    user: dict = Depends(require_operator),
    q: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    team: str | None = None,
    assignee: str | None = None,
    service: str | None = None,
    sort: str = "-updated_at",
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
):
    filters = {}
    if q:
        filters["$text"] = {"$search": q}
    for key, value in {"status": status, "severity": severity, "service": service}.items():
        if value:
            filters[key] = value
    if team:
        filters["team_id"] = oid(team)
    if assignee:
        filters["assignee_id"] = oid(assignee)
    direction = -1 if sort.startswith("-") else 1
    sort_key = sort.removeprefix("-")
    total = await db().incidents.count_documents(filters)
    cursor = db().incidents.find(filters).sort(sort_key, direction).skip((page - 1) * limit).limit(limit)
    return {"items": serialize(await cursor.to_list(limit)), "total": total, "page": page, "limit": limit}


@router.post("")
async def post_incident(payload: IncidentIn, user: dict = Depends(require_operator)):
    incident = await create_incident(payload.model_dump(), user["_id"])
    return serialize(incident)


@router.get("/{incident_id}")
async def get_incident(incident_id: str, user: dict = Depends(require_operator)):
    key = f"incident:{incident_id}"
    cached = await get_json(key)
    if cached:
        return cached
    incident = await get_incident_or_404(incident_id)
    comments = await db().comments.find({"incident_id": oid(incident_id)}).sort("created_at", -1).to_list(100)
    tasks = await db().tasks.find({"incident_id": oid(incident_id)}).sort("created_at", -1).to_list(100)
    activities = await db().activities.find({"incident_id": oid(incident_id)}).sort("created_at", -1).to_list(100)
    runs = await db().ai_runs.find({"incident_id": oid(incident_id)}).sort("created_at", -1).to_list(5)
    actions = await db().ai_actions.find({"incident_id": oid(incident_id), "status": "pending"}).to_list(20)
    payload = serialize({**incident, "comments": comments, "tasks": tasks, "activities": activities, "ai_runs": runs, "pending_actions": actions})
    await set_json(key, payload, 60)
    return payload


@router.patch("/{incident_id}")
async def patch_incident(incident_id: str, payload: IncidentPatch, user: dict = Depends(require_operator)):
    return serialize(await mutate_incident(incident_id, payload.model_dump(), user))


@router.post("/{incident_id}/comments")
async def add_comment(incident_id: str, payload: CommentIn, user: dict = Depends(require_operator)):
    await get_incident_or_404(incident_id)
    doc = {"incident_id": oid(incident_id), "actor_id": oid(user["_id"]), "body": payload.body, "created_at": now()}
    result = await db().comments.insert_one(doc)
    await write_activity(incident_id, user["_id"], "comment.added", payload.body)
    await audit(user["_id"], "comment.added", "incident", incident_id)
    await invalidate_incident(incident_id)
    doc["_id"] = result.inserted_id
    await emit("comment.added", serialize(doc), f"incident:{incident_id}")
    return serialize(doc)


@router.post("/{incident_id}/tasks")
async def create_task(incident_id: str, payload: TaskIn, user: dict = Depends(require_operator)):
    await get_incident_or_404(incident_id)
    doc = {**payload.model_dump(), "incident_id": oid(incident_id), "created_at": now(), "updated_at": now()}
    if doc.get("assignee_id"):
        doc["assignee_id"] = oid(doc["assignee_id"])
    result = await db().tasks.insert_one(doc)
    await write_activity(incident_id, user["_id"], "task.created", payload.title)
    await audit(user["_id"], "task.created", "incident", incident_id)
    await invalidate_incident(incident_id)
    doc["_id"] = result.inserted_id
    await emit("task.updated", serialize(doc), f"incident:{incident_id}")
    return serialize(doc)


@router.patch("/{incident_id}/tasks/{task_id}")
async def update_task(incident_id: str, task_id: str, payload: TaskPatch, user: dict = Depends(require_operator)):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    if update.get("assignee_id"):
        update["assignee_id"] = oid(update["assignee_id"])
    update["updated_at"] = now()
    await db().tasks.update_one({"_id": oid(task_id), "incident_id": oid(incident_id)}, {"$set": update})
    task = await db().tasks.find_one({"_id": oid(task_id)})
    await write_activity(incident_id, user["_id"], "task.updated", "Task updated", update)
    await audit(user["_id"], "task.updated", "incident", incident_id, update)
    await invalidate_incident(incident_id)
    await emit("task.updated", serialize(task), f"incident:{incident_id}")
    return serialize(task)
