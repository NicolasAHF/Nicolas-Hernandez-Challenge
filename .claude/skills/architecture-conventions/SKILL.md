---
name: architecture-conventions
description: The architecture and design patterns this codebase follows — layered architecture, repository pattern, service layer, DTO, dependency injection, SRP. Use when explaining the architecture, deciding where new code goes, or reviewing whether a change fits the codebase's style.
---

# Architecture conventions

The description of how this codebase is built. Apply these patterns and, when in
doubt, match the existing files.

## What this is: layered architecture

A FastAPI app organized as a classic layered architecture with a one-way dependency
flow. Business logic lives in the service layer. It's simple and explicit.

```
api/routers/   HTTP layer        → parse request, call service, return response
services/      business logic     → ALL rules, validation, calculations; raises 404
repositories/  data access        → DB queries only; returns ORM model or None
models/        ORM entities        → SQLAlchemy columns + relationships
schemas/       DTOs                → Pydantic request/response models
core/          infra              → config, db session, security, cache helpers
api/deps.py    composition root    → wires services via FastAPI Depends
```

## Patterns the code follows

- **Layered architecture** — strict one-way dependencies; upper layers know lower
  ones, never the reverse.
- **Repository pattern** — `PlanRepository`, `TaskRepository`, etc. Concrete classes
  taking a `Session`; expose intention-revealing query/persist methods.
- **Service layer** — `PlanService`, `TaskService`. Own the business logic,
  validation and calculations, translate missing data into `HTTPException(404)`, and
  return validated schemas.
- **DTO pattern** — Pydantic schemas (`StudyPlanCreate/Read/Update`) decouple the API
  contract from ORM models. Read models use `from_attributes`.
- **Dependency injection** — at the HTTP boundary only: routers receive a service via
  `Depends(get_x_service)`; `deps.py` is the composition root.
- **SRP** — each module/class has a single clear responsibility.

## Where does new code go?

| You're adding…                        | Put it in…                          |
|---------------------------------------|-------------------------------------|
| A new HTTP route                      | `api/routers/` (one-line delegate)  |
| A calculation, rule, or 404 decision  | `services/`                         |
| A DB query / persistence              | `repositories/`                     |
| A request/response shape              | `schemas/`                          |
| A new column/table                    | `models/` + an Alembic migration    |
| Config, cache, cross-cutting infra    | `core/`                             |
| Wiring a new service into routes      | `api/deps.py`                       |

If a change seems to need a new pattern, that's a **design decision** — raise it
with the maintainer first (see CLAUDE.md Working agreements) rather than introducing
it silently.

## Examples this skill should handle

1. **Placement**: given "add plan metrics", correctly route the computation to the
   service, the query to the repository, the shape to a schema, the route to the
   router — no logic in router/repo.
2. **Consistency**: a new endpoint reuses the existing Repository + Service + DTO +
   DI structure instead of inventing a parallel one.
3. **Design check**: when a task would introduce a new pattern not already in the
   codebase, flag it as a design decision to confirm before implementing.
