# PlanOS Frontend Integration

## Backend Architecture

PlanOS backend is a **FastAPI + async SQLAlchemy + PostgreSQL + Redis + Celery** application.

- **Base URL**: `http://localhost:8000`
- **API Prefix**: `/api/v1`
- **OpenAPI Docs**: `http://localhost:8000/docs`
- **Health Check**: `GET /health`

---

## Authentication Flow

### Token-Based Auth (JWT)

**Login**: `POST /api/v1/auth/login`

Request:
```json
{"email": "admin@acme.com", "password": "password123"}
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Refresh**: `POST /api/v1/auth/refresh`

Request:
```json
{"refresh_token": "eyJ..."}
```

**Current User**: `GET /api/v1/auth/me` (requires Bearer token)

Response:
```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "email": "admin@acme.com",
  "full_name": "Alice Admin",
  "role": "ADMIN",
  "organization": {
    "id": "uuid",
    "name": "Acme Corp",
    "slug": "acme-corp",
    "created_at": "...",
    "updated_at": "..."
  }
}
```

### Roles

`ADMIN` | `PLANNER` | `ANALYST` | `VIEWER`

### Error Format

All errors return:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Plan not found"
  }
}
```

Status codes: `401` (unauthorized), `403` (forbidden), `404` (not found), `409` (conflict/stale version), `422` (validation), `500` (server error)

---

## Available API Endpoints

### Plans

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/plans` | plan:create | Create plan |
| GET | `/api/v1/plans` | plan:read | List plans (paginated, `?status=`) |
| GET | `/api/v1/plans/{id}` | plan:read | Get plan |
| PATCH | `/api/v1/plans/{id}` | plan:update | Update plan (requires `expected_version`) |

**PlanCreate**: `{"name": "...", "description": "..."}`
**PlanUpdate**: `{"name": "...", "status": "draft|active|archived", "expected_version": 1}`
**PlanResponse**: `{"id", "organization_id", "name", "description", "status", "current_version", "created_at", "updated_at"}`
**PlanListResponse**: `{"items": [...], "total": 10, "page": 1, "page_size": 20}`

### Scenarios

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/scenarios` | scenario:create | Create scenario |
| GET | `/api/v1/scenarios` | scenario:read | List scenarios |
| GET | `/api/v1/scenarios/{id}` | scenario:read | Get scenario |
| POST | `/api/v1/scenarios/{id}/run` | scenario:run | Queue scenario execution |

**ScenarioCreate**: `{"name": "...", "base_plan_id": "uuid", "description": "...", "changes": {"demand_growth": 0.15}}`
**ScenarioResponse**: `{"id", "organization_id", "base_plan_id", "name", "description", "status", "changes", "results", "created_at", "updated_at"}`
**ScenarioRunResponse**: `{"job_id": "uuid", "status": "queued"}`

### Runs (Async Jobs)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/runs/{job_id}` | scenario:read | Get job status |

**RunStatusResponse**: `{"job_id": "...", "status": "PENDING|STARTED|SUCCESS|FAILURE", "result": {...}}`

### Agents

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/agents/run` | agent:execute | Run agent |
| GET | `/api/v1/agents/runs/{run_id}` | agent:read | Get agent run |

**AgentRunRequest**: `{"agent_type": "planning|finance|workforce|analyst", "input_text": "..."}`
**AgentRunResponse**: `{"id", "organization_id", "agent_id", "status", "input_text", "output_text", "error_message", "started_at", "completed_at", "created_at", "steps": [...]}`

---

## Backend Gaps (Not Available)

The following frontend sections will use local development fixtures until backend endpoints are implemented:

| Feature | Status | Frontend Approach |
|---------|--------|-------------------|
| Dashboard stats | Missing | Derive from plans/scenarios/runs lists |
| Organizations management | Missing | Show from login/seed data |
| Approvals | Missing | UI with local fixture + documented gap |
| Evaluations | Missing | UI with local fixture + documented gap |
| Data Imports | Missing | UI with local fixture + documented gap |
| Audit Logs | Missing | UI with local fixture + documented gap |
| Scenario comparison | Missing | Client-side comparison of two scenarios |
| Real-time updates | Missing | TanStack Query polling (5s interval) |
| Plan metrics/dimensions | Missing | Aggregate from scenario results |
| Settings page | Partial | Profile from `/auth/me` only |

---

## Seed Data (For Demo)

Organizations: `Acme Corp` (slug: `acme-corp`), `Globex Inc`
Users: `admin@acme.com/password123` (ADMIN), `planner@acme.com/password123` (PLANNER), `analyst@acme.com/password123` (ANALYST), `viewer@acme.com/password123` (VIEWER), `admin@globex.com/password123` (ADMIN)
