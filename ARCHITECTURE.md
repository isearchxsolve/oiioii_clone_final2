# ARCHITECTURE.md

## Overview

**oiioii_clone_final2** is an AI animation agent platform that orchestrates a creative pipeline from script to final rendered video with sound. The system follows a layered FastAPI + React architecture with clear separation between API, domain services, and data access. It implements a job-based async workflow engine for media generation, an asset store for generated artifacts, and a polished workspace UI featuring an agent timeline and asset gallery.

**Core capabilities:**
- User authentication (register/login with JWT)
- Project CRUD and ownership
- Creative workflow orchestration: Script → Character → Scene → Storyboard → Render → Sound
- Async job system with structured failure handling for media generation
- Asset store with versioned artifacts
- MediaGenerationService consuming external AI APIs via env-configured keys
- Real-time workspace UI with agent timeline and asset gallery

---

## Components

### Backend (FastAPI) — `backend/`

| Module | Path | Responsibility |
|--------|------|----------------|
| **App Factory** | `backend/app/main.py` | FastAPI instance, middleware, router registration, lifespan events |
| **Health API** | `backend/app/api/health.py` | `GET /api/health` — liveness/readiness |
| **Auth API** | `backend/app/api/auth.py` | `POST /api/auth/register`, `POST /api/auth/login` |
| **Projects API** | `backend/app/api/projects.py` | `GET/POST /api/projects`, `GET/PATCH/DELETE /api/projects/{id}` |
| **Workflows API** | `backend/app/api/workflows.py` | `POST /api/projects/{id}/workflows`, `GET /api/projects/{id}/workflows/{wf_id}` |
| **Jobs API** | `backend/app/api/jobs.py` | `GET /api/jobs/{job_id}`, `GET /api/projects/{id}/jobs` |
| **Assets API** | `backend/app/api/assets.py` | `GET/POST /api/projects/{id}/assets`, `GET /api/assets/{asset_id}/download` |
| **Auth Service** | `backend/app/services/auth_service.py` | Password hashing, JWT creation/validation, user lookup |
| **Project Service** | `backend/app/services/project_service.py` | Project CRUD, ownership checks, workflow initiation |
| **Workflow Service** | `backend/app/services/workflow_service.py` | Orchestrates 6-stage pipeline, creates Job records, emits events |
| **Job Service** | `backend/app/services/job_service.py` | Job lifecycle (pending/running/succeeded/failed), retry logic, failure structuring |
| **Asset Service** | `backend/app/services/asset_service.py` | Asset metadata, storage abstraction, versioning, signed URLs |
| **Media Generation Service** | `backend/app/services/media_generation.py` | Calls external AI APIs (script→char, char→scene, storyboard, render, TTS/sound) using env keys |
| **User Repository** | `backend/app/repositories/user_repo.py` | SQLAlchemy user queries |
| **Project Repository** | `backend/app/repositories/project_repo.py` | Project + membership queries |
| **Workflow Repository** | `backend/app/repositories/workflow_repo.py` | Workflow + stage state persistence |
| **Job Repository** | `backend/app/repositories/job_repo.py` | Job CRUD, status transitions, failure payloads |
| **Asset Repository** | `backend/app/repositories/asset_repo.py` | Asset metadata, version chains |
| **Models** | `backend/app/models/` | SQLAlchemy declarative models: `User`, `Project`, `Workflow`, `WorkflowStage`, `Job`, `Asset` |
| **Schemas** | `backend/app/schemas/` | Pydantic request/response models per API |
| **Security** | `backend/app/core/security.py` | JWT settings, password hashing (bcrypt), token decode |
| **Config** | `backend/app/core/config.py` | Pydantic BaseSettings loading from `.env` |
| **Database** | `backend/app/core/database.py` | Async SQLAlchemy engine, sessionmaker, Base |
| **Exceptions** | `backend/app/core/exceptions.py` | Custom exception classes + FastAPI exception handlers |
| **Celery App** | `backend/app/workers/celery_app.py` | Celery instance, broker/result backend config |
| **Job Tasks** | `backend/app/workers/job_tasks.py` | Celery tasks executing workflow stages via MediaGenerationService |

### Frontend (React + Vite) — `frontend/`

| Module | Path | Responsibility |
|--------|------|----------------|
| **App Entry** | `frontend/src/main.tsx` | React root, providers (Auth, Query, Router) |
| **Routing** | `frontend/src/routes.tsx` | React Router v6 routes: `/login`, `/register`, `/projects`, `/projects/:id/workspace` |
| **API Client** | `frontend/src/lib/api.ts` | Axios instance with JWT interceptor, typed API functions |
| **Auth Context** | `frontend/src/contexts/AuthContext.tsx` | User state, login/register/logout, token persistence (localStorage) |
| **Project List** | `frontend/src/pages/ProjectsPage.tsx` | Project cards, create modal, delete confirmation |
| **Workspace** | `frontend/src/pages/WorkspacePage.tsx` | Main canvas: left timeline, center stage preview, right asset gallery |
| **Agent Timeline** | `frontend/src/components/timeline/AgentTimeline.tsx` | Horizontal stage nodes (Script→Character→Scene→Storyboard→Render→Sound) with status badges, click-to-retry |
| **Asset Gallery** | `frontend/src/components/gallery/AssetGallery.tsx` | Grid of versioned assets per stage, preview, download, "use in next stage" |
| **Stage Panel** | `frontend/src/components/workspace/StagePanel.tsx` | Per-stage input forms (prompt editors, parameter controls) and output preview |
| **Job Polling Hook** | `frontend/src/hooks/useJobPolling.ts` | SWR/React Query polling for job status, SSE fallback |
| **UI Primitives** | `frontend/src/components/ui/` | Button, Input, Modal, Card, Badge, Spinner, Tooltip (Tailwind + Headless UI) |
| **Types** | `frontend/src/types/` | TypeScript interfaces mirroring backend schemas |

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **PostgreSQL** | `postgres:16` | Primary relational store (users, projects, workflows, jobs, assets) |
| **Redis** | `redis:7` | Celery broker, result backend, rate limiting, session cache |
| **MinIO / S3** | `minio/minio` | Object storage for generated media assets (video, audio, images) |
| **Celery Workers** | `celery -A app.workers.celery_app worker` | Async job execution (1 worker per stage type, scalable) |
| **Nginx** | `nginx:alpine` | Reverse proxy, static file serving, TLS termination |
| **Docker Compose** | `docker-compose.yml` | Local dev + production stack orchestration |

---

## Data Flow

### 1. Authentication Flow
```
POST /api/auth/register  →  AuthService.hash_password()  →  UserRepo.create()  →  JWT issued
POST /api/auth/login     →  UserRepo.get_by_email()  →  verify_password()  →  JWT issued
```
JWT (access token, 15min) + refresh token (7d, httpOnly cookie) returned. All subsequent requests require `Authorization: Bearer <access>`.

### 2. Project Creation
```
POST /api/projects  →  ProjectService.create(owner_id)  →  ProjectRepo.create()  →  201 + ProjectRead
```

### 3. Workflow Initiation (Creative Pipeline)
```
POST /api/projects/{id}/workflows
  → ProjectService.verify_ownership()
  → WorkflowService.create_workflow(project_id, input_script)
  → WorkflowRepo.create(Workflow + 6 WorkflowStage records: script, character, scene, storyboard, render, sound)
  → JobService.enqueue_stage_job(workflow_id, stage="script")
  → Celery task job_tasks.execute_stage.delay(job_id)
  → 202 Accepted + WorkflowRead (stages=pending)
```

### 4. Stage Execution (per stage, sequential)
```
Celery worker picks job_tasks.execute_stage(job_id)
  → JobService.mark_running(job_id)
  → MediaGenerationService.call_stage_api(stage, inputs, api_keys_from_env)
  → On success:
       AssetService.store_output(asset_bytes, metadata) → AssetRepo.create()
       WorkflowStageRepo.update(stage_id, status="succeeded", output_asset_id)
       JobService.mark_succeeded(job_id, output_asset_id)
       If not final stage: JobService.enqueue_next_stage(workflow_id)
  → On failure (API error, timeout, validation):
       JobService.mark_failed(job_id, failure_code, failure_detail, retryable)
       WorkflowStageRepo.update(stage_id, status="failed", error_payload)
       WorkflowRepo.update(workflow_id, status="failed")
       Emit WebSocket event for UI toast
```

### 5. Asset Retrieval
```
GET /api/projects/{id}/assets  →  AssetService.list_by_project()  →  AssetRepo.query()  →  AssetRead[]
GET /api/assets/{asset_id}/download  →  AssetService.get_signed_url()  →  MinIO presigned GET  →  302 redirect
```

### 6. Workspace UI Polling
```
WorkspacePage mounts → useJobPolling(workflow_id) polls GET /api/workflows/{id} every 2s
  → Updates AgentTimeline stage badges (pending/running/succeeded/failed)
  → On stage success: AssetGallery fetches new asset via GET /api/projects/{id}/assets?stage=X
  → User clicks "Retry" on failed stage → POST /api/jobs/{job_id}/retry → JobService.retry()
```

---

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Backend Framework** | FastAPI | 0.111+ |
| **Async ORM** | SQLAlchemy | 2.0+ (async) |
| **Migration** | Alembic | 1.13+ |
| **Validation** | Pydantic | 2.7+ |
| **Auth** | python-jose (JWT), passlib[bcrypt] | latest |
| **Task Queue** | Celery | 5.3+ |
| **Broker/Result** | Redis | 7 |
| **Object Storage** | MinIO (S3-compatible) | latest |
| **Database** | PostgreSQL | 16 |
| **Frontend Framework** | React | 18.2+ |
| **Build Tool** | Vite | 5+ |
| **Language** | TypeScript | 5.4+ |
| **Routing** | React Router | 6.22+ |
| **State/Data Fetching** | TanStack Query (React Query) | 5+ |
| **Styling** | Tailwind CSS | 3.4+ |
| **UI Primitives** | Headless UI | 1.7+ |
| **Icons** | Lucide React | 0.344+ |
| **WebSocket** | native WebSocket + fallback polling | — |
| **Containerization** | Docker, Docker Compose | — |
| **Reverse Proxy** | Nginx | alpine |

---

## Layering

```
backend/
├── app/
│   ├── main.py                    # FastAPI app factory, lifespan, middleware
│   ├── core/
│   │   ├── config.py              # Settings (Pydantic BaseSettings)
│   │   ├── database.py            # Async engine, sessionmaker, Base
│   │   ├── security.py            # JWT, password hashing, token decode
│   │   └── exceptions.py          # AppException, handlers, error codes
│   ├── models/                    # SQLAlchemy declarative models
│   │   ├── user.py                # User
│   │   ├── project.py             # Project, ProjectMember
│   │   ├── workflow.py            # Workflow, WorkflowStage
│   │   ├── job.py                 # Job
│   │   └── asset.py               # Asset, AssetVersion
│   ├── schemas/                   # Pydantic request/response models
│   │   ├── auth.py                # RegisterRequest, LoginRequest, TokenResponse
│   │   ├── project.py             # ProjectCreate, ProjectRead, ProjectUpdate
│   │   ├── workflow.py            # WorkflowCreate, WorkflowRead, StageRead
│   │   ├── job.py                 # JobRead, JobRetryRequest
│   │   └── asset.py               # AssetRead, AssetCreate, AssetVersionRead
│   ├── repositories/              # Data access (SQLAlchemy async)
│   │   ├── user_repo.py           # UserRepository
│   │   ├── project_repo.py        # ProjectRepository
│   │   ├── workflow_repo.py       # WorkflowRepository
│   │   ├── job_repo.py            # JobRepository
│   │   └── asset_repo.py          # AssetRepository
│   ├── services/                  # Domain logic (no HTTP, no DB sessions)
│   │   ├── auth_service.py        # AuthService
│   │   ├── project_service.py     # ProjectService
│   │   ├── workflow_service.py    # WorkflowService
│   │   ├── job_service.py         # JobService
│   │   ├── asset_service.py       # AssetService
│   │   └── media_generation.py    # MediaGenerationService
│   ├── api/                       # FastAPI routers (thin, validation → service)
│   │   ├── health.py              # GET /api/health
│   │   ├── auth.py                # POST /api/auth/register, /login
│   │   ├── projects.py            # CRUD /api/projects
│   │   ├── workflows.py           # POST /api/projects/{id}/workflows, GET /workflows/{id}
│   │   ├── jobs.py                # GET /api/jobs/{id}, GET /api/projects/{id}/jobs, POST /retry
│   │   └── assets.py              # GET/POST /api/projects/{id}/assets, GET /assets/{id}/download
│   └── workers/                   # Celery tasks
│       ├── celery_app.py          # Celery instance, config
│       └── job_tasks.py           # execute_stage, retry_job tasks
```

**Dependency direction:** `api` → `services` → `repositories` → `models`. Services never import API or workers. Workers import services only.

---

## Auth & Security

- **Password hashing:** bcrypt via `passlib`, cost factor 12 (`AuthService.hash_password`)
- **JWT:** RS256 asymmetric keys (private key for signing, public for verification). Keys loaded from `AUTH_PRIVATE_KEY_PATH`, `AUTH_PUBLIC_KEY_PATH` (PEM files). Access token TTL: 15 min. Refresh token: 7 days, stored in httpOnly `Secure; SameSite=Lax` cookie.
- **Token payload:** `sub` (user_id), `email`, `iat`, `exp`, `type` ("access"|"refresh")
- **Authorization:** `Depends(get_current_user)` extracts user from access token. Project endpoints verify ownership via `ProjectService.verify_ownership(user_id, project_id)`.
- **CORS:** Restricted to `FRONTEND_ORIGIN` from env. Credentials allowed.
- **Rate limiting:** Redis-backed sliding window (10 req/s per IP on auth, 30 req/s on API) via custom middleware.
- **Secrets:** All API keys for external AI providers (`OPENAI_API_KEY`, `RUNWAY_API_KEY`, `ELEVENLABS_API_KEY`, `REPLICATE_API_KEY`) loaded via `Settings` from `.env`, never committed.
- **HTTPS:** Enforced in production via Nginx TLS termination. `SECURE_COOKIES=true` in prod.

---

## Data Model

### `User` (`app/models/user.py`)
```python
id: UUID (PK)
email: str (unique, index)
hashed_password: str
full_name: str | None
created_at: DateTime (default=now)
updated_at: DateTime (onupdate=now)
is_active: bool (default=True)
```

### `Project` (`app/models/project.py`)
```python
id: UUID (PK)
name: str
description: str | None
owner_id: UUID (FK → User.id, index)
created_at: DateTime
updated_at: DateTime
```
**ProjectMember** (many-to-many for future collaboration):
```python
project_id: UUID (FK, PK)
user_id: UUID (FK, PK)
role: str (owner|editor|viewer)
joined_at: DateTime
```

### `Workflow` (`app/models/workflow.py`)
```python
id: UUID (PK)
project_id: UUID (FK, index)
name: str
input_script: str (initial user prompt)
status: Enum(pending, running, succeeded, failed)
current_stage: str | None (one of 6 stage keys)
created_at: DateTime
updated_at: DateTime
completed_at: DateTime | None
```

### `WorkflowStage` (`app/models/workflow.py`)
```python
id: UUID (PK)
workflow_id: UUID (FK, index)
stage_key: Enum(script, character, scene, storyboard, render, sound)
sequence: int (0-5)
status: Enum(pending, running, succeeded, failed)
input_payload: JSONB (parameters for this stage)
output_asset_id: UUID | None (FK → Asset.id)
error_payload: JSONB | None (structured failure)
started_at: DateTime | None
completed_at: DateTime | None
```

### `Job` (`app/models/job.py`)
```python
id: UUID (PK)
workflow_id: UUID (FK, index)
stage_id: UUID (FK, index)
stage_key: Enum(script, character, scene, storyboard, render, sound)
status: Enum(pending, running, succeeded, failed)
celery_task_id: str | None
attempt: int (default=1)
max_attempts: int (default=3)
failure_code: str | None (e.g., "UPSTREAM_API_ERROR", "VALIDATION_FAILED", "TIMEOUT")
failure_detail: JSONB | None
retryable: bool (default=True)
created_at: DateTime
started_at: DateTime | None
completed_at: DateTime | None
```

### `Asset` (`app/models/asset.py`)
```python
id: UUID (PK)
project_id: UUID (FK, index)
workflow_id: UUID | None (FK, index)
stage_key: Enum(script, character, scene, storyboard, render, sound)
version: int (1-based)
filename: str
content_type: str (video/mp4, audio/mpeg, image/png, application/json)
size_bytes: int
storage_path: str (MinIO