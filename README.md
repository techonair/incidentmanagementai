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
admin@monklens.dev
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
   -d "{\"email\":\"admin@monklens.dev\",\"password\":\"admin123\"}" \
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

### Architecture Decisions

- **Frontend:** Next.js 14 App Router, TypeScript, Tailwind, Recharts, and a small Zustand-ready client structure.
- **Backend:** FastAPI routers for transport, incident services for business rules, Motor for async MongoDB access, and ARQ for background jobs.
- **Primary database:** MongoDB database `purplelens` is retained as an internal compatibility name. Collections are separated by concern: `users`, `teams`, `incidents`, `alerts`, `tasks`, `comments`, `activities`, `ai_runs`, `ai_actions`, and `audit_log`.
- **History model:** Tasks, comments, activities, alerts, AI runs, and audit records are referenced by `incident_id` rather than embedded into one unbounded incident document.
- **Identifiers and time:** MongoDB `ObjectId` values are serialized to strings at the API boundary; timestamps are stored as UTC datetimes.
- **Authentication:** JWTs are stored in an HTTP-only cookie, with bearer-token support for API clients. Backend dependencies enforce operator and admin access; frontend checks are not trusted.
- **Authorization rules:** Operators can work incidents, comments, and tasks. Only admins can assign `sev1`. Resolved incidents are locked except for an admin reopening them.
- **External alerts:** An alert with the same fingerprint and service within 30 minutes links to the existing incident; otherwise a new incident is created. Correlation activity is queued through ARQ.

### Required Views

- **Operations Overview:** Implemented at `/` with open count, critical count, aging count, status/severity charts, and recent activity.
- **Incident Queue:** Implemented at `/incidents` with backend text search, severity filtering, sorting, server-side pagination parameters, board/list views, and incident links. The UI currently requests up to 50 records and does not expose page controls.
- **Incident Investigation:** Implemented at `/incidents/{id}` with editable summary, status/severity, comments, tasks, timeline, AI findings, and approval actions. Related alerts are available through the backend data model but are not yet rendered in the detail UI.
- **Users & Teams:** Implemented at `/admin` with users, teams, and workload visibility. It is currently read-only; user/team creation, membership editing, and role editing remain incomplete.
- **AI Operations:** Implemented at `/ai` as a first-class queue for investigations, findings, and pending approvals.

### Required Workflow Decisions

1. **Authentication and access:** Seed one admin and nine operators. Login returns a JWT HTTP-only cookie; every protected route uses backend role dependencies.
2. **Alert to incident:** Use fingerprint + service + 30-minute correlation. A new incident receives the alert title, summary, service, and severity.
3. **Incident investigation:** Use a three-column detail workspace, with timeline/collaboration in the center and AI controls on the right.
4. **Assignment and collaboration:** Incident fields are patched through the backend; comments and tasks are separate collections and emit activity/audit records.
5. **AI investigation:** Queue the job, load application context, produce structured findings, write autonomous notes/tasks, and create pending approval actions.
6. **Human approval:** `change_severity` and `assign_incident` require approval. `add_note` and `create_task` are autonomous because they do not directly change incident ownership or priority.
7. **Resolution:** Status changes are recorded as activities and audit records. Resolved incidents are protected from normal operator edits.
8. **Audit trail:** Record incident creation/updates, alert linking, comments, task changes, AI completion, approvals, rejections, and executed actions.

### Cache Decisions

Redis is used for read-heavy data, not as the source of truth:

| Key | Data | TTL | Invalidation |
| --- | --- | --- | --- |
| `dash:overview` | Dashboard aggregates and recent activity | 15s | Any incident mutation |
| `incident:{id}` | Incident detail plus comments/tasks/activity/AI state | 60s | Any incident, comment, or task mutation |
| `team:workload` | Open incidents grouped by team | 30s | Incident mutations |
| `ref:teams` | User/team reference data | 5m | Manual/expiry-based |

Cache misses query MongoDB and repopulate Redis. Redis connection, read, write, delete, and publish failures are swallowed so MongoDB-backed pages continue to serve. This is intentionally a graceful degradation strategy rather than a cache-as-database design.

### Real-Time Decisions

WebSockets use `/ws` with `global` and `incident:{id}` rooms. Redis Pub/Sub on the `events` channel lets the backend and worker broadcast across processes. Events include incident creation/update, comments, tasks, AI state changes, pending actions, and executed actions. Current clients refetch on received events; automatic reconnect with a full refetch is still a remaining hardening item.

### AI Decisions

The AI workflow is grounded in application data. The worker retrieves the current incident, up to 20 related alerts, up to 5 similar incidents using service/severity/text search, and open workload grouped by team. A deterministic structured fallback is used when `OPENAI_API_KEY` is absent, so the demo remains reproducible and does not depend on an external provider.

The finding contract is:

```text
summary
likely_cause
severity_suggestion
similar_incident_ids[]
recommended_actions[]
```

AI writes through controlled application operations rather than unrestricted database access: `add_note`, `create_task`, `change_severity`, and `assign_incident`. The latter two are approval-gated. Pending, approved, rejected, completed, and failed states are stored and broadcast. Timeout/invalid-output validation, retry-once behavior, and stronger idempotency handling remain incomplete and are explicitly not claimed as done.

### Seed and Demo Decisions

On an empty database, startup creates 6 teams, 10 users, 120 incidents, and 300 alerts across five services. The seed is deterministic for repeatable demo data. Existing legacy `@purplelens.dev` user records are migrated to `@monklens.dev` during startup; the internal Mongo database name remains `purplelens` for compatibility.

The intended evaluator demo is:

```text
POST alert -> correlate/create incident -> assign -> start AI investigation
-> retrieve alerts/similar incidents/workload -> produce findings
-> create autonomous task/note -> request approval -> approve severity action
-> update incident -> write activity/audit -> broadcast realtime event
```
