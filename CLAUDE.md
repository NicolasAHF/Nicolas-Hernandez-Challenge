# CLAUDE.md — AI Study Planner

Engineering guide for agents and humans working in this repo. Read this first; it
encodes the conventions so you don't rediscover them each session.

## What this is

**AI Study Planner** — a full-stack web app for organizing study goals, plans, and
tasks. Users create study plans (a goal + weekly hour budget + optional target
date), break them into tasks with estimated hours, and track completion.

This file plus `docs/state/` is the durable memory of the project: an agent forgets
between runs, the repo doesn't.

## Current feature work

Active features being built (full spec + status in `docs/state/PROGRESS.md`):

1. **Plan rebalancing** — `GET /plans/{id}/rebalance`: when a plan's total task
   hours exceed its weekly budget, suggest how to reduce per-task hours or
   redistribute effort across weeks. Deterministic logic in the service layer.
2. **Plan metrics** — `GET /plans/{id}/metrics`: total/completed tasks, completion
   %, total/completed hours. Computed in the service layer, single source of truth.
3. **Metrics caching** — Redis cache-aside in front of the metrics endpoint, with
   key strategy, TTL, invalidation on task writes, and graceful fallback.

## Stack

| Layer    | Tech                                            |
|----------|-------------------------------------------------|
| Backend  | Python 3.12, FastAPI 0.115, SQLAlchemy 2, uv    |
| DB       | PostgreSQL 16 (SQLite in tests), Alembic        |
| Frontend | React 18, TypeScript, Vite, Mantine 7, TanStack Query |
| Infra    | Docker Compose                                  |

## Architecture & layering rules (non-negotiable)

The codebase enforces a strict one-way layering. Keep new work inside these lanes —
this is the team's standard and what keeps the code testable and easy to navigate.

```
api/routers/   → HTTP only: parse request, call service, return response. No logic.
services/      → ALL business logic. Raises HTTPException(404, ...) for missing rows.
repositories/  → Database access ONLY. No business rules. Returns ORM models or None.
models/        → SQLAlchemy ORM models.
schemas/       → Pydantic request/response models (DTOs).
core/          → config, db session, security/infra helpers (e.g. cache).
api/deps.py    → wires services into routers via FastAPI Depends.
```

Hard rules:
- **No business logic in routers.** Routers are one-liners that delegate to a service.
- **No business logic in repositories.** They query/persist and return models.
- **Calculations and decisions live in services.** One source of truth — never
  duplicate a computation across layers (or in the frontend).
- A repository method returns `Model | None`; the **service** turns `None` into a 404.
- Schemas use `model_config = {"from_attributes": True}` for read models; services
  return `Schema.model_validate(orm_obj)`.
- New service is wired in `api/deps.py` with a `get_<x>_service` provider.

### Patterns in use

This is a **layered architecture**. See the `architecture-conventions` skill for the
full picture. Patterns the code follows:
- **Layered architecture** with one-way dependencies (HTTP → service → data).
- **Repository pattern** (concrete classes) for data access.
- **Service layer** holding all business logic.
- **DTO pattern** via Pydantic schemas at the API boundary.
- **Dependency injection** at the HTTP boundary (FastAPI `Depends` + `deps.py`).
- **SRP** — each module/class has one clear responsibility.

## Commands

```bash
# Run everything
docker compose up --build            # frontend :5173, api :8000, docs :8000/docs

# Backend tests (run from backend/)
cd backend && uv sync --all-groups && uv run pytest tests/ -v

# Backend without Docker
cd backend && DATABASE_URL=postgresql://postgres:postgres@localhost:5432/study_planner \
  uv run uvicorn app.main:app --reload

# Migrations
cd backend && uv run alembic revision --autogenerate -m "<msg>"   # then review!
cd backend && uv run alembic upgrade head

# Frontend only
cd frontend && npm install && npm run dev
```

Local seed credentials: `admin` / `admin123`. Four sample plans with tasks at
various completion states.

## Testing conventions

- `tests/conftest.py` swaps Postgres for SQLite and overrides `get_db`. A `client`
  fixture yields a `TestClient`; `reset_db` recreates tables per test.
- Test through the HTTP layer with `client.post/get/...`, assert on status + JSON.
- Write tests **first** for new endpoints. Put plan-level tests in
  `tests/test_plans.py`.

## Working agreements

- **Design decisions are reviewed before implementation.** When a task involves a
  non-trivial design choice — an algorithm, a data shape, an API contract, a caching
  strategy, a TTL, a library, a schema/migration — STOP and present the options to
  the maintainer first. Lay out 2–3 concrete alternatives with their trade-offs and
  a recommendation, and let them pick. Don't implement the choice until it's made.
  Once decided, record it in `docs/state/DECISIONS.md`. Mechanical/obvious work
  (wiring, boilerplate, following an existing pattern) doesn't need this.
- Write conventional, scoped, descriptive commit messages.
- One PR per feature; branch per feature (e.g. `feat/plan-rebalance`). Keep diffs
  focused and reviewable.
- Record non-obvious decisions and trade-offs in `docs/state/DECISIONS.md` as you go
  (algorithm choices, TTL justification, etc.).
- Update `docs/state/PROGRESS.md` after each meaningful step.

## The agent layer in this repo

- **Skills** (`.claude/skills/`) — reusable recipes for this codebase:
  - `architecture-conventions` — the patterns this codebase uses; where new code goes.
  - `backend-vertical-slice` — add an endpoint across router→service→repository + tests.
  - `redis-cache-aside` — the caching pattern for the metrics cache.
  - `frontend-plan-view` — surface backend data in the React/Mantine plan detail view.
- **Subagents** (`.claude/agents/`) — a second opinion that didn't write the code:
  - `layering-reviewer` — checks a diff against the layering rules + clean code.
  - `acceptance-verifier` — runs tests and checks a feature against its spec.
- **State** (`docs/state/`) — `PROGRESS.md` (status + next steps),
  `DECISIONS.md` (trade-offs / ADR-lite).
