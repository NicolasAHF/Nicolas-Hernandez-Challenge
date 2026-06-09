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

- **Rebalance algorithm:** what exactly does "suggested reduction per task" vs
  "redistribution across weeks" mean numerically? Need a deterministic, explainable
  rule (e.g. scale each task's hours down proportionally so the total fits
  `hours_per_week`, and/or spread the overflow across N weeks until a target date).
  Document the chosen formula and why.
- **Cache TTL:** pick a value and justify. Because every relevant write invalidates
  the key, the TTL is a backstop for missed invalidations, not the main freshness
  mechanism → a short/moderate TTL (e.g. 300s) balances bounded staleness against
  churn. Record the final number and reasoning here.
- **Redis client / fakeredis in tests:** how to test cache hit/invalidation/fallback
  deterministically without a live Redis (e.g. `fakeredis`, or an in-memory fake
  behind the cache interface). Decide and note it.

_(Replace each bullet with a dated decision entry once resolved.)_
