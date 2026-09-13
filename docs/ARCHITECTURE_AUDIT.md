# PlanOS — Architecture Audit (Phase 0)

Date: 2026-09-13 | Auditor: AI agent | Repo: `Shivani767/PlanOS`

## 1. Current architecture (as found)

Layered FastAPI monolith, async end-to-end:

```
Client -> Nginx (proxy only) -> FastAPI (/api/v1) -> Service layer
  -> SQLAlchemy 2.x async -> PostgreSQL 16
  -> Redis (broker/result) -> Celery (scenario sims)
```

`planos/app/`: `api/routes/{auth,plans,scenarios,runs,agents}`,
`core/{config,security,permissions,exceptions,logging}`,
`db/session.py` (async engine, pool 20+10), `models/` (12 files),
`schemas/`, `services/{auth,organization,plan,scenario,agent}`,
`planning/{engine,calculator}`, `workers/{celery_app,scenario_tasks}`,
`evaluation/{datasets,evaluator,models}`.

## 2. Existing components — verdict

| Component | State |
|---|---|
| Auth (JWT access+refresh, bcrypt) | WORKING |
| RBAC (ADMIN/PLANNER/ANALYST/VIEWER x 17 perms) | WORKING, unit-tested |
| Tenant isolation (org_id checks in services) | WORKING, security-tested |
| Planning engine (deterministic, pure fns) | WORKING, unit-tested |
| Optimistic locking (Plan.current_version) | PARTIAL (no DB row-level guard) |
| Error format `{"error":{code,message}}` | PARTIAL (missing request_id) |
| Structured logging (structlog JSON) | WORKING |
| Celery scenario sims | WORKING (code smell: `__import__` hack) |
| Agent service | BROKEN (imports non-existent `AgentToolCall`, `started_at`; router never mounted) |
| Evaluator | BROKEN (imports at file bottom) |
| Docs/ | MISSING |
| Tools/MCP/RAG/Memory/Policy/Approvals API/Cache/Metrics/Jobs API/Idempotency | MISSING |

## 3. APIs (mounted)

`POST /api/v1/auth/{register,login,refresh}`, `GET /auth/me`,
`POST/GET /plans`, `GET/PATCH /plans/{id}`,
`POST/GET /scenarios`, `GET /scenarios/{id}`, `POST /scenarios/{id}/run` (200, should be 202),
`GET /runs/{job_id}`, `GET /health`. Agents router exists but NOT mounted.

## 4. DB schema

`organizations`, `users`, `plans` + `plan_versions` (uq plan,version),
`scenarios` + `scenario_changes` + `scenario_results`,
`agents`/`agent_runs`/`agent_steps`/`checkpoints`,
`approval_requests`, `audit_logs`, `import_jobs`,
`products/regions/departments/time_periods` (uq per org),
`planning_data` (composite lookup index). All tenant tables carry
`organization_id` with CASCADE FKs. Migration `97066edbb994` covers
only orgs+users — schema drift for the rest.

## 5. Auth flow / RBAC / async / Redis / Celery / Docker / CI / infra

JWT(H256, 30m access/7d refresh, scopes `org:`, `role:`) -> `get_current_user`
(DB lookup per request) -> `require_permission_factory`. Async everywhere
(asyncpg, async sessions, httpx tests). Redis = broker+backend only (no cache).
Celery: `execute_scenario` on `planning` queue, 5m hard limit, eager untested.
Docker Compose: api/worker/scheduler/postgres/redis/nginx all present;
image runs as non-root but single-stage + dev install. CI: lint+typecheck+unit+
integration+docker build — real gates. Terraform VPC/SG/RDS-shape, k8s base
manifests (typo `llatest`), nginx proxy+health, Prometheus scrape config only
(no app `/metrics`), OTel deps installed but disabled.

## 6. Correctness bugs fixed in Phase 0

1. `services/agent.py`: imported non-existent `AgentToolCall`, set
   non-existent `AgentRun.started_at`, used `step.content` vs model fields.
2. `api/routes/agents.py` -> `service.get_run` (method is `get_run`) + response
   shape mismatch.
3. `evaluation/evaluator.py`: `uuid/datetime` imported at file bottom.
4. `workers/scenario_tasks.py`: `__import__("sqlalchemy")` hack.
5. `main.py`: `agents` router imported but never mounted.
6. `calculator.py`: duplicated return line.
7. `k8s/base.yaml`: image tag `llatest`.

## 7. Planned changes (priority order)

P0: request_id middleware, 202+Idempotency-Key on run, Tool Registry +
policy gate + 4 orchestrated agents, approvals API (transactional),
jobs API (DB-backed), structured agent state/trace, scenario compare,
plan soft-delete, migration covering full schema, row-level optimistic lock.
P1: MCP server, Redis cache-aside, Prometheus `/metrics`, OTel wiring,
concurrency/idempotency/agent test suites, flagship demo endpoint.
P2: RAG (tenant-scoped), memory tiers, Locust benchmarks + PERFORMANCE.md,
Docker hardening, docs/ + ADRs.
