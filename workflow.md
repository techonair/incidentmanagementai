# MonkLens — AI Incident & Operations Platform
## Engineering Plan (for AI coding agent)

## Mission
Build a working Jira-style incident management platform in ONE vertical slice:
Next.js + FastAPI + MongoDB + Redis + WebSockets + background worker + AI investigation.
Prioritize: working happy path end-to-end over breadth. Prefer working code over features.

## Hard Rules
- Do NOT build every feature if time is short. Cut in this order: drag-and-drop
  board, charts, pagination polish, extra filters, email. NEVER cut: auth,
  incident CRUD + search, AI investigation, AI approval flow, cache
  invalidation, websocket updates.
- After EVERY phase: run the app, hit the API with curl, verify it works.
  Fix before moving on.
- No placeholder code that silently does nothing. Mock the LLM with a
  deterministic fallback instead.
- Secrets via .env only. Commit a .env.example.
- docker-compose.yml must start everything: mongo, redis, backend, worker,
  frontend. `docker compose up` =&gt; seeded app at localhost:3000.

## Tech Stack (fixed)
- Backend: FastAPI, Motor (async Mongo), Pydantic v2, python-jose + passlib,
  ARQ (Redis queue) for worker
- Frontend: Next.js 14 App Router, TypeScript, Tailwind, Zustand, recharts
- DB: MongoDB. Cache/queue/pubsub: Redis.

## Phase 1 — Skeleton & Auth
 [x] Monorepo: /backend /frontend docker-compose.yml
 [x] FastAPI app factory, routers folder, CORS, health endpoint
 [x] Collections: users, teams, incidents, alerts, tasks, comments,
      activities, ai_runs, audit_log
 [x] Indexes: incidents {status,severity,team_id,assignee_id,updated_at},
      text index title+summary; alerts {fingerprint,created_at};
      activities/comments/tasks {incident_id,created_at}
 [x] Seed: 6 teams, 10 users (admin@purplelens.dev/admin123),
      ~120 incidents, ~300 alerts, services: payments-api, auth-service,
      checkout, search, notifications
 [x] Auth: POST /auth/login (JWT httpOnly cookie), GET /auth/me,
      require_admin / require_operator dependencies

## Phase 2 — Incidents Core
 [x] GET /incidents: server-side text search, filters (status, severity,
      team, assignee, service), sort, page+limit. All queries use indexes.
 [x] GET/POST/PATCH /incidents, PATCH = status/severity/team/assignee
 [x] Rules: only admin assigns sev1; resolved locked except admin reopen
 [x] POST /alerts: fingerprint+service match within 30min -&gt; link to
      existing incident, else create new. Run correlation async via ARQ.
 [x] Every mutation writes `activities` + `audit_log` docs
 [x] Comments POST, tasks CRUD
- [ ] Verify: create/filter/paginate via curl; alert dedup links vs creates
 [x] Cache helper, graceful fallback (Redis down -&gt; Mongo, never crash)
 [x] Keys: dash:overview (15s), incident:{id} (60s), team:workload (30s),
- [ ] Cache helper, graceful fallback (Redis down -&gt; Mongo, never crash)
 [x] Invalidation: every incident mutation deletes incident:{id} + dash
      ref:teams (5min)
 [x] GET /dashboard/overview: open count, sev1/2 count, by-status,
      keys + affected team:workload
- [ ] GET /dashboard/overview: open count, sev1/2 count, by-status,
 [x] WS /ws, rooms: incident:{id} + global queue channel
 [x] Redis pub/sub so worker process broadcasts too
 [x] Events: incident.created/.updated, comment.added, task.updated,
## Phase 4 — Real-time
- [ ] WS /ws, rooms: incident:{id} + global queue channel
 [x] POST /incidents/{id}/ai-investigation -&gt; ARQ job, ai_run status queued
 [x] Worker loop: get_incident -&gt; get_related_alerts -&gt;
      ai.state_changed, ai.action_pending, ai.action_executed
- [ ] Frontend reconnect -&gt; full refetch
 [x] LLM interface: no OPENAI_API_KEY -&gt; deterministic mock returning

 [x] Output: {summary, likely_cause, severity_suggestion,
- [ ] POST /incidents/{id}/ai-investigation -&gt; ARQ job, ai_run status queued
 [x] requires_approval=true -&gt; pending card in UI
 [x] POST /ai-actions/{id}/approve | /reject -&gt; execute on approve,
      get_team_workload -&gt; LLM
- [ ] LLM interface: no OPENAI_API_KEY -&gt; deterministic mock returning
 [x] Shell: left nav (Overview, Incidents, Users & Teams) + topbar
 [ ] /incidents: kanban by status + list toggle, filter bar, pagination,
      similar_incident_ids[], recommended_actions[]}
 [x] /incidents/[id]: 3 columns - editable summary, timeline+comments+tasks,
      create_task (autonomous), change_severity, assign_incident (approval)
 [x] /: stat cards + 2 small charts from /dashboard/overview
- [ ] POST /ai-actions/{id}/approve | /reject -&gt; execute on approve,
 [x] README: setup, .env vars, seed, ascii architecture diagram, cache
- [ ] Failures: timeout/invalid JSON -&gt; failed, retry once; idempotency
      key incident:{id}
- [ ] Verify: investigation -&gt; findings -&gt; approve severity change -&gt;
      incident updated, all in timeline

## Phase 6 — Frontend (Jira-style, simple)
- [ ] Shell: left nav (Overview, Incidents, Users & Teams) + topbar
- [ ] /incidents: kanban by status + list toggle, filter bar, pagination,
      click -&gt; /incidents/[id]
- [ ] /incidents/[id]: 3 columns - editable summary, timeline+comments+tasks,
      right AI sidebar (run button, findings, approve/reject cards)
- [ ] /: stat cards + 2 small charts from /dashboard/overview
- [ ] /admin: users/teams tables, create/edit, workload counts
- [ ] Skeletons, empty states, error toasts
- [ ] Verify: full demo scenario in browser

## Phase 7 — Polish & Docs
- [ ] README: setup, .env vars, seed, ascii architecture diagram, cache
      strategy, AI workflow + tools explanation
- [ ] Full demo path: POST alert -&gt; live incident -&gt; assign -&gt; AI -&gt;
      findings -&gt; approve -&gt; executed -&gt; timeline complete
- [ ] Kill Redis once: app still serves pages

## Definition of Done
- docker compose up -&gt; login as admin -&gt; seeded board visible
- Full demo path works in one browser session
- Cache invalidation provable, WS across 2 tabs, AI approval flow complete
- README runs in &lt; 10 min