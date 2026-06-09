---
name: redis-cache-aside
description: Add a Redis cache-aside layer to a service method in this FastAPI app, with a defined key strategy, justified TTL, explicit invalidation, and graceful fallback when Redis is down. Use for the plan-metrics cache or any read endpoint that needs caching without breaking service/repository separation.
---

# Redis cache-aside for plan metrics

A clean cache layer that the service uses, that never breaks if Redis is
unavailable, and that stays out of the repository.

## Where the cache lives

- A thin `core/cache.py` wraps the Redis client and exposes `get_json` / `set_json`
  / `delete`. It swallows connection errors and logs, returning `None` on failure
  so callers fall back to the DB. **Caching is an infrastructure concern in `core/`,
  not the repository** (repositories stay pure DB access).
- The **service** orchestrates cache-aside; the repository never knows about Redis.

## Cache-aside read flow (in the service)

```python
def get_metrics(self, plan_id: int) -> PlanMetrics:
    key = self._metrics_key(plan_id)
    cached = cache.get_json(key)          # returns None on miss OR Redis error
    if cached is not None:
        return PlanMetrics(**cached)
    metrics = self._compute_metrics(plan_id)   # DB path (also raises 404)
    cache.set_json(key, metrics.model_dump(), ttl=settings.METRICS_CACHE_TTL)
    return metrics
```

- Always recompute from DB on miss/error — Redis being down must never surface to
  the user. Wrap Redis calls so exceptions become a miss, never a 500.

## Key strategy

- Format: `plan:{plan_id}:metrics` — one key per plan's metrics payload.
- Document it in `core/cache.py` and in `docs/state/DECISIONS.md`.

## TTL

- Pick a value and **justify it** in `DECISIONS.md`. Metrics are invalidated on
  every write, so TTL is a safety net for missed invalidations, not the primary
  freshness mechanism. A short-to-moderate TTL (e.g. 300s) is defensible; state the
  reasoning (bounded staleness vs. cache churn). Make it configurable via `settings`.

## Invalidation

Delete the key whenever the metrics could change. In `TaskService`, after a
successful commit:

- task **created** → `cache.delete(metrics_key(plan_id))`
- task **updated** (completion toggled) → delete
- task **deleted** → delete

Centralize the key builder so service and cache agree on the format. Invalidate
*after* the DB commit succeeds, not before.

## Graceful fallback

- If Redis is unreachable: reads recompute from DB; writes still succeed and just
  skip the delete (best-effort). No request should fail because of Redis.
- Make the Redis URL configurable (`settings.REDIS_URL`), add a `redis` service to
  `docker-compose.yml`, and ensure the app boots even if it's absent.

## Don't

- Don't put Redis calls in routers or repositories.
- Don't let a Redis exception propagate to the response.
- Don't duplicate the metrics computation — the cache wraps the *existing* metrics
  service method (depends on `backend-vertical-slice`).

## Worked examples this skill should handle

1. **Cache hit**: second call to `GET /plans/{id}/metrics` is served from Redis
   (DB/compute path not re-run — verify via spy or fakeredis).
2. **Invalidation**: after creating/toggling/deleting a task, the next metrics call
   reflects the change (key was deleted, value recomputed).
3. **Fallback**: with Redis unavailable, `GET /plans/{id}/metrics` still returns
   200 with correct values, and task writes still succeed.
