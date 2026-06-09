---
name: backend-vertical-slice
description: Add or modify a backend endpoint in this FastAPI app following the router→service→repository layering. Use when adding a GET/POST/PATCH endpoint under /plans, /users, or /auth, writing a service method, a repository query, or a Pydantic schema, and the matching pytest tests.
---

# Backend vertical slice

How to add an endpoint to this codebase without violating the layering. Staying
inside these lanes is the team's standard and what keeps the code testable.

## The layers (one-way dependency)

```
router (api/routers/*.py)  → calls service, returns its result. NO logic.
service (services/*.py)    → ALL business logic; raises HTTPException(404) on missing.
repository (repositories/*.py) → DB queries only; returns ORM model or None.
schema (schemas/*.py)      → Pydantic in/out DTOs.
deps (api/deps.py)         → provides services via Depends.
```

## Recipe (write the test first)

1. **Test first** in `tests/test_<area>.py`. Hit the HTTP layer:
   ```python
   def test_plan_metrics(client, user):
       plan = client.post("/plans", json={"user_id": user["id"], "goal": "G", "hours_per_week": 10}).json()
       client.post(f"/plans/{plan['id']}/tasks", json={"title": "T", "estimated_hours": 4})
       r = client.get(f"/plans/{plan['id']}/metrics")
       assert r.status_code == 200
       assert r.json()["total_tasks"] == 1
   ```
   Run `cd backend && uv run pytest tests/ -v` and watch it fail.

2. **Schema** (`schemas/study_plan.py`): add a Pydantic response model. Read models
   that map from ORM objects need `model_config = {"from_attributes": True}`.

3. **Repository** (`repositories/*.py`): add only the query you need. Return the ORM
   model(s) or `None`. No calculations, no decisions here.
   ```python
   def get_with_tasks(self, plan_id: int) -> StudyPlan | None:
       return self.db.query(StudyPlan).filter(StudyPlan.id == plan_id).first()
   ```

4. **Service** (`services/*.py`): put the logic here. Fetch via repo, turn `None`
   into a 404, compute, return a validated schema.
   ```python
   def get_metrics(self, plan_id: int) -> PlanMetrics:
       plan = self.repo.get_by_id(plan_id)
       if not plan:
           raise HTTPException(status_code=404, detail="Plan not found")
       ...compute from plan.tasks...
       return PlanMetrics(...)
   ```

5. **Router** (`api/routers/*.py`): a one-line delegate with `response_model`.
   ```python
   @router.get("/{plan_id}/metrics", response_model=PlanMetrics)
   def get_metrics(plan_id: int, svc: PlanService = Depends(get_plan_service)):
       return svc.get_metrics(plan_id)
   ```
   Note: route ordering — literal paths like `/{plan_id}/metrics` are fine, but
   keep them distinct from `/{plan_id}`.

6. **Wire deps** if it's a new service: add a `get_<x>_service` in `api/deps.py`.

7. Run the tests green, then `uv run pytest tests/ -v` for the whole suite.

## Conventions to match (copy the existing style)

- Services receive a `Session` in `__init__` and build their repositories there.
- Use `data.model_dump(exclude_unset=True)` for partial updates (see `PlanRepository.update`).
- `raise HTTPException(status_code=404, detail="<Thing> not found")` — exact pattern.
- Return `Schema.model_validate(orm)` from services, never the raw ORM object.
- Type hints everywhere; `Model | None`, `list[Schema]`.

## Worked examples this skill should handle

1. **Add a read endpoint** (e.g. `GET /plans/{id}/metrics`): test written first,
   logic ends up in the service, repository only queries, router is a one-liner.
2. **Missing resource**: requesting a non-existent plan returns `404` raised by the
   service (not the repository, not the router).
3. **New service wiring**: a brand-new service is provided through `api/deps.py` and
   injected with `Depends`, not constructed inside the router.
