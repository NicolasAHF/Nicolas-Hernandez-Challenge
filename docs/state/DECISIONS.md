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

## Open questions to resolve while implementing

These are flagged now so the decisions are deliberate, not accidental:

- **Rebalance algorithm:** what exactly does "suggested reduction per task" vs
  "redistribution across weeks" mean numerically? Need a deterministic, explainable
  rule (e.g. scale each task's hours down proportionally so the total fits
  `hours_per_week`, and/or spread the overflow across N weeks until a target date).
  Document the chosen formula and why.
- **Metrics — `completed_hours` definition:** sum of `estimated_hours` for tasks
  where `completed = true` (there's no separate "actual hours" field). Confirm and
  state this.
- **Completion percentage basis:** by task count or by hours? `total tasks`,
  `completed tasks` and `completion percentage` are tracked separately, so
  percentage = by task count. State it.
- **Cache TTL:** pick a value and justify. Because every relevant write invalidates
  the key, the TTL is a backstop for missed invalidations, not the main freshness
  mechanism → a short/moderate TTL (e.g. 300s) balances bounded staleness against
  churn. Record the final number and reasoning here.
- **Redis client / fakeredis in tests:** how to test cache hit/invalidation/fallback
  deterministically without a live Redis (e.g. `fakeredis`, or an in-memory fake
  behind the cache interface). Decide and note it.

_(Replace each bullet with a dated decision entry once resolved.)_
