from ..db import serialize


async def deterministic_investigation(incident: dict, alerts: list[dict], similar: list[dict], workload: list[dict]) -> dict:
    service = incident.get("service", "service")
    severity = incident.get("severity", "sev3")
    suggested = "sev2" if severity in {"sev3", "sev4"} and len(alerts) >= 2 else severity
    return {
        "summary": f"{service} is showing a correlated incident pattern across {len(alerts)} alert(s).",
        "likely_cause": f"Recent {service} errors match previous operational noise and require owner triage.",
        "severity_suggestion": suggested,
        "similar_incident_ids": [str(item["_id"]) for item in similar[:5]],
        "recommended_actions": [
            {"tool": "add_note", "args": {"body": f"AI reviewed alerts and similar {service} incidents."}, "requires_approval": False},
            {"tool": "create_task", "args": {"title": f"Check {service} error budget and recent deploys"}, "requires_approval": False},
            {"tool": "change_severity", "args": {"severity": suggested}, "requires_approval": True},
        ],
        "workload": serialize(workload),
    }
