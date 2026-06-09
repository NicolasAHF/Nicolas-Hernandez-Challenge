# PROGRESS

Durable status tracker for in-flight features. An agent forgets between runs; this
file doesn't. Update it after each meaningful step. One PR per feature.

Status legend: ⬜ not started · 🟡 in progress · ✅ done · 🧪 tests green

---

## Feature: Plan rebalancing suggestion  ⬜

> As a user, I want the system to suggest how to rebalance my study plan when it is
> overloaded, so that I can better distribute my effort.

Requirements:
- [ ] `GET /plans/{id}/rebalance` endpoint
- [ ] When total task hours exceed `hours_per_week`, return: a suggested reduction
      per task **or** a suggested redistribution across weeks
- [ ] Deterministic (no AI / randomness / time dependence)
- [ ] Logic in the service layer
- [ ] Response format clear and structured
- [ ] Suggestions visible in the plan detail view (frontend)

Branch: `feat/plan-rebalance` · PR: —
Notes / next step:

---

## Feature: Plan progress & metrics  🟡

> As a user, I want to see progress and key metrics of my study plan, so that I can
> understand how I am advancing.

Requirements:
- [ ] `GET /plans/{id}/metrics` endpoint
- [ ] Response includes: total tasks, completed tasks, completion percentage,
      total estimated hours, completed hours
- [ ] Calculations done in the service layer
- [ ] Performant, no duplicated logic across layers
- [ ] Metrics visible in the plan detail view (frontend)

Branch: `feat/plan-metrics` · PR: —
Notes / next step: design decided (see DECISIONS.md 2026-06-09) — compute in
service from loaded tasks; `%` by task count, integer 0–100, 0 tasks → 0;
`completed_hours` = sum of estimated_hours where completed. Next: implement the
vertical slice, tests first.

---

## Feature: Redis caching for plan metrics  ⬜

> As a user, I want plan metrics to load quickly even for large plans, so that the
> application remains responsive.

Requirements:
- [ ] Introduce Redis as a caching layer
- [ ] Cache the response of `GET /plans/{id}/metrics`
- [ ] Define a cache key strategy (e.g. `plan:{id}:metrics`)
- [ ] Invalidate cache when tasks are created, updated, or deleted, and on task
      completion-status changes
- [ ] TTL strategy defined and justified (see `DECISIONS.md`)
- [ ] Graceful fallback if Redis is unavailable
- [ ] Service/repository separation not broken
- [ ] UI reflects up-to-date metrics after task changes

Branch: `feat/redis-cache` · PR: —
Notes / next step:

---

## Suggested order & dependencies

1. **Metrics** first — the caching feature wraps its endpoint, so build it first.
2. **Rebalancing** — independent; can go anytime.
3. **Redis caching** — depends on the metrics endpoint existing.

## Working notes (latest first)

- _(empty — add dated entries as work progresses)_
