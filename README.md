# MonkLens

AI-assisted incident operations platform built as one working vertical slice:
Next.js, FastAPI, MongoDB, Redis, WebSockets, ARQ worker, dashboard cache, and deterministic AI investigation.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:3000` and log in with:

```text
admin@purplelens.dev
admin123
```

The backend seeds 6 teams, 10 users, about 120 incidents, and about 300 alerts on first startup.

## Services

```text
browser :3000
   |
frontend Next.js
   |
backend FastAPI :8000
   |         |
MongoDB   Redis cache/pubsub/ARQ
             |
          worker
```

## Environment

See `.env.example`.

Important values:

- `MONGO_URL`
- `MONGO_DB`
- `REDIS_URL`
- `JWT_SECRET`
- `FRONTEND_ORIGIN`
- `NEXT_PUBLIC_API_URL`

## Demo Path

1. Log in at `http://localhost:3000`.
2. Open Incidents and choose any incident.
3. Add a comment and a task; the timeline updates.
4. Click Run in the AI panel.
5. The worker writes findings, creates an autonomous task, and creates a pending severity action.
6. Approve the pending action.
7. The incident severity changes, the audit/activity trail updates, cache is invalidated, and websocket listeners refetch.

You can also post an alert:

```bash
curl -i -c cookies.txt -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@purplelens.dev\",\"password\":\"admin123\"}" \
  http://localhost:8000/auth/login

curl -b cookies.txt -H "Content-Type: application/json" \
  -d "{\"fingerprint\":\"payments-api:demo\",\"service\":\"payments-api\",\"title\":\"Checkout payment errors\",\"summary\":\"5xx spike\",\"severity\":\"sev2\"}" \
  http://localhost:8000/alerts
```

Posting the same fingerprint/service within 30 minutes links to the existing incident; otherwise a new incident is created.

## Cache Strategy

- `dash:overview`: 15 seconds
- `incident:{id}`: 60 seconds
- `team:workload`: 30 seconds
- `ref:teams`: 5 minutes

Incident mutations delete incident detail, dashboard, and workload keys. Redis failures fall back to MongoDB reads and do not crash request handlers.

## AI Workflow

`POST /incidents/{id}/ai-investigation` enqueues an ARQ job. The worker gathers the incident, related alerts, similar incidents, and workload. Without `OPENAI_API_KEY`, it uses a deterministic JSON-producing investigation.

Autonomous tools:

- `add_note`
- `create_task`

Approval tools:

- `change_severity`
- `assign_incident`

Approval and rejection endpoints write audit/activity records and broadcast websocket events.

## Useful API Checks

```bash
curl http://localhost:8000/health
curl -b cookies.txt http://localhost:8000/incidents?limit=5
curl -b cookies.txt http://localhost:8000/dashboard/overview
```

To test Redis fallback, stop Redis after the app is running. Core pages should still serve from MongoDB; cache and queue-backed work will degrade.
