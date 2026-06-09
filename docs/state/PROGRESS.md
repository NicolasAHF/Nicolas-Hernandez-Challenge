# PROGRESS

Durable status tracker for in-flight features. An agent forgets between runs; this
file doesn't. Update it after each meaningful step. One PR per feature.

Status legend: ⬜ not started · 🟡 in progress · ✅ done · 🧪 tests green

---

## Feature: Plan rebalancing suggestion  🧪

> As a user, I want the system to suggest how to rebalance my study plan when it is
> overloaded, so that I can better distribute my effort.

Requirements:
- [x] `GET /plans/{id}/rebalance` endpoint
- [x] When total task hours exceed `hours_per_week`, suggest a week-by-week schedule
      that spreads whole tasks across weeks (redistribution; see DECISIONS)
- [x] Deterministic (no AI / randomness / time dependence)
- [x] Logic in the service layer (`PlanService.get_rebalance`)
- [x] Response format clear and structured (`PlanRebalance` schema)
- [x] Suggestions visible in the plan detail view (overloaded panel)

Branch: `feat/plan-rebalance` · PR: —
Notes / next step: implemented (see DECISIONS.md 2026-06-09). 32 backend tests green
(6 rebalance tests, incl. oversized-task splitting), frontend builds. Awaiting
review/merge.

---

## Feature: Plan progress & metrics  🧪

> As a user, I want to see progress and key metrics of my study plan, so that I can
> understand how I am advancing.

Requirements:
- [x] `GET /plans/{id}/metrics` endpoint
- [x] Response includes: total tasks, completed tasks, completion percentage,
      total estimated hours, completed hours
- [x] Calculations done in the service layer (`PlanService.get_metrics`)
- [x] Performant, no duplicated logic across layers (frontend consumes the endpoint)
- [x] Metrics visible in the plan detail view (frontend)

Branch: `feat/plan-metrics` · PR: —
Notes / next step: implemented (see DECISIONS.md 2026-06-09). 26 backend tests green
(4 new metrics tests), frontend builds. Awaiting review/merge.

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
