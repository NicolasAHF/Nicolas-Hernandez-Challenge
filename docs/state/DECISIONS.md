# DECISIONS — trade-offs & rationale

ADR-lite log for non-obvious engineering choices (algorithm design, TTL values,
test strategy, etc.). Add an entry whenever a decision is made that a future
maintainer would otherwise have to reverse-engineer. Newest first.

Template:

```
## YYYY-MM-DD — <decision title>  [feature]
**Context:** what prompted the choice.
**Options considered:** A / B / C.
**Decision:** what was chosen.
**Trade-offs:** what we gave up; why it's acceptable here.
```

---

## 2026-06-09 — Redis cache for plan metrics  [cache]

**Context:** `GET /plans/{id}/metrics` recomputes from the DB every call. Cache it in
Redis with cache-aside, without breaking service/repository separation, and degrade
gracefully if Redis is down.

**Decisions:**
- **Injected `Cache` abstraction.** `core/cache.py` defines a `Cache` protocol with
  `RedisCache` (real) and `InMemoryCache` (tests) implementations, injected into the
  services via `deps.py` like everything else. Chosen over a module-level Redis client
  so the cache is swappable and testable without a live Redis or extra test deps, and
  to match the codebase's dependency-injection style. Caching stays an infra concern
  in `core/`; repositories remain pure DB access.
- **Cache-aside in the service.** `PlanService.get_metrics` checks the cache, computes
  from the DB on a miss, and stores the result. The 404 path is unaffected (a missing
  plan is never cached).
- **Key strategy:** `plan:{id}:metrics`, built by one shared helper so the service and
  the invalidation agree.
- **TTL = 300s.** Every task write invalidates the key, so the TTL is a backstop for
  missed invalidations / orphaned keys, not the primary freshness mechanism. 5 minutes
  bounds staleness while avoiding churn. Configurable via `settings.METRICS_CACHE_TTL`.
- **Invalidation** on task create and update (toggle) in `TaskService`, after the DB
  commit. There is no delete-task endpoint in the app, so delete invalidation is not
  wired; the hook would go in the same place if one were added.
- **Graceful fallback:** `RedisCache` swallows `redis.RedisError` — reads return a
  miss (recompute from DB), writes are best-effort no-ops. No request fails because
  Redis is unavailable, and the app boots without it (lazy connection).

**Trade-offs:** the `Cache` abstraction adds a small indirection the codebase didn't
have before; accepted because it keeps Redis out of the services/repositories and
makes the behaviour testable deterministically.

---

## 2026-06-09 — Plan rebalancing: weekly schedule across weeks  [rebalance]

**Context:** `GET /plans/{id}/rebalance` must, when a plan's total task hours exceed
`hours_per_week`, suggest either a per-task reduction **or** a redistribution across
weeks. Deterministic, logic in the service.

**Decisions:**
- **Redistribute across weeks, not reduce per task.** A task's `estimated_hours` is
  the effort the task genuinely needs — it is not a flexible budget. Suggesting "do
  this 12h task in 6h" is meaningless; the work still takes 12h. So instead of
  shrinking tasks we keep every task's hours intact and spread them over more weeks.
- **Split tasks larger than the weekly budget.** A task whose `estimated_hours`
  exceeds `hours_per_week` can't fit in a single week, so it is broken into parts of
  at most `hours_per_week` each (full chunks plus a remainder), named `"<title> -1"`,
  `"<title> -2"`, … Every resulting unit is ≤ the weekly budget, so no week ever
  exceeds it.
- **Greedy week-by-week packing.** After splitting, iterate the units in task-id
  order; fill the current week until adding the next unit would exceed
  `hours_per_week`, then start a new week. Deterministic. `weeks_needed` = number of
  weeks produced. A split remainder can share a week with the next task's unit.
- **Response shape:** `overloaded`, `hours_per_week`, `total_estimated_hours`,
  `weeks_needed`, and `schedule` (a list of `{week, tasks:[{task_id,title,hours}],
  total_hours}`). Split parts keep the parent `task_id` and carry the `-N` suffix in
  `title`. When not overloaded → `overloaded: false`, `schedule: []`. `404` if the
  plan does not exist.

**Trade-offs:** greedy first-fit by id keeps tasks in their natural order but may not
pack weeks as tightly as first-fit-decreasing; chosen for predictability and because
study tasks are usually done in order. Splitting assumes a task's hours can be done in
independent chunks, which is a reasonable simplification for study time.

---

## 2026-06-09 — Plan metrics: computation, percentage basis & format  [metrics]

**Context:** `GET /plans/{id}/metrics` must return total/completed tasks, completion
percentage, and total/completed estimated hours, with calculations in the service
layer and no logic duplicated across layers.

**Decisions:**
- **Compute in the service (Python).** The repository fetches the plan with its
  tasks; the service counts and sums in memory and builds the `PlanMetrics` DTO.
  Chosen over SQL aggregation in the repository because it keeps all calculation in
  the service layer (per the layering rules) and stays simple. Performance for large
  plans is addressed separately by the Redis cache feature, not by pushing
  aggregation into the repo.
- **`completed_hours` = sum of `estimated_hours` where `completed = true`.** There is
  no separate "actual hours" field on a task, so completed hours are the estimates of
  the done tasks. `total_estimated_hours` = sum over all tasks.
- **`completion_percentage` is by task count:** `completed_tasks / total_tasks * 100`.
  The spec tracks `completed tasks` and `completion percentage` separately, and this
  matches what the UI already shows. **Returned as an integer 0–100** (rounded), to
  match the existing `Math.round` rendering. **A plan with 0 tasks → 0%** (no
  divide-by-zero).

**Trade-offs:** in-memory computation loads all of a plan's tasks per request; for
very large plans that's less efficient than a single SQL aggregate, but it's simpler,
keeps the calculation in the service, and is exactly what the caching feature exists
to optimize.

---

## Open questions to resolve while implementing

These are flagged now so the decisions are deliberate, not accidental:

- **Cache TTL:** pick a value and justify. Because every relevant write invalidates
  the key, the TTL is a backstop for missed invalidations, not the main freshness
  mechanism → a short/moderate TTL (e.g. 300s) balances bounded staleness against
  churn. Record the final number and reasoning here.
- **Redis client / fakeredis in tests:** how to test cache hit/invalidation/fallback
  deterministically without a live Redis (e.g. `fakeredis`, or an in-memory fake
  behind the cache interface). Decide and note it.

_(Replace each bullet with a dated decision entry once resolved.)_
