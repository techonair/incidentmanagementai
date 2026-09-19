from datetime import timedelta
from random import choice, randint, seed

from .auth import hash_password
from .db import now

SERVICES = ["payments-api", "auth-service", "checkout", "search", "notifications"]
STATUSES = ["open", "investigating", "mitigated", "resolved"]
SEVERITIES = ["sev1", "sev2", "sev3", "sev4"]


async def seed_database(database) -> None:
    await database.users.update_many(
        {"email": {"$regex": "@purplelens\\.dev$"}},
        [{"$set": {"email": {"$replaceOne": {"input": "$email", "find": "@purplelens.dev", "replacement": "@monklens.dev"}}}}],
    )
    await database.users.update_one({"name": "Purple Admin"}, {"$set": {"name": "Monk Admin"}})
    if await database.users.count_documents({}):
        return
    seed(42)
    teams = [{"name": name, "service": svc} for name, svc in [
        ("Payments", "payments-api"),
        ("Identity", "auth-service"),
        ("Checkout", "checkout"),
        ("Search", "search"),
        ("Comms", "notifications"),
        ("Platform", "shared"),
    ]]
    team_result = await database.teams.insert_many(teams)
    team_ids = team_result.inserted_ids
    users = [{
        "name": "Monk Admin",
        "email": "admin@monklens.dev",
        "role": "admin",
        "team_id": team_ids[0],
        "password_hash": hash_password("admin123"),
    }]
    for i in range(1, 10):
        users.append({
            "name": f"Operator {i}",
            "email": f"operator{i}@monklens.dev",
            "role": "operator",
            "team_id": choice(team_ids),
            "password_hash": hash_password("operator123"),
        })
    user_result = await database.users.insert_many(users)
    user_ids = user_result.inserted_ids
    base = now()
    incidents = []
    for i in range(120):
        service = choice(SERVICES)
        created = base - timedelta(hours=randint(1, 240))
        incidents.append({
            "title": f"{service} incident {i + 1}",
            "summary": f"Elevated errors observed in {service}.",
            "service": service,
            "status": choice(STATUSES),
            "severity": choice(SEVERITIES),
            "team_id": choice(team_ids),
            "assignee_id": choice(user_ids),
            "created_at": created,
            "updated_at": created + timedelta(minutes=randint(5, 720)),
        })
    incident_result = await database.incidents.insert_many(incidents)
    alerts = []
    for i in range(300):
        service = choice(SERVICES)
        created = base - timedelta(minutes=randint(1, 20000))
        alerts.append({
            "fingerprint": f"{service}:{randint(1, 80)}",
            "service": service,
            "title": f"{service} alert {i + 1}",
            "summary": "Synthetic seeded alert",
            "severity": choice(SEVERITIES),
            "incident_id": choice(incident_result.inserted_ids),
            "created_at": created,
        })
    await database.alerts.insert_many(alerts)
