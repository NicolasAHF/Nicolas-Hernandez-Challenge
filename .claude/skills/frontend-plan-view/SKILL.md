---
name: frontend-plan-view
description: Surface backend data (metrics, rebalance suggestions) in the React plan detail view using Mantine 7 and TanStack Query. Use when adding a new API call to frontend/src/api/client.ts and rendering it in PlanDetail.tsx, matching the existing query-key and styling conventions.
---

# Frontend plan view

How to wire new backend data (metrics, rebalance suggestions) into the plan detail
page so it's visible to the user.

## API client (`frontend/src/api/client.ts`)

- Add a typed method on the `api` object. Use the existing `req<T>` helper (it adds
  the Bearer token and the `/api` base, throws on non-2xx).
- Export a `type` for the response shape that mirrors the backend Pydantic schema.
  ```ts
  export type PlanMetrics = {
    total_tasks: number;
    completed_tasks: number;
    completion_percentage: number;
    total_estimated_hours: number;
    completed_hours: number;
  };
  // on the api object:
  getPlanMetrics: (id: number) => req<PlanMetrics>(`/plans/${id}/metrics`),
  ```

## Rendering in `PlanDetail.tsx`

- Fetch with TanStack Query, mirroring the existing `["plan", id]` / `["tasks", id]`
  keys:
  ```ts
  const { data: metrics } = useQuery({
    queryKey: ["metrics", id],
    queryFn: () => api.getPlanMetrics(id),
    enabled: !!id,
  });
  ```
- **Invalidate** the new query wherever it can change. The toggle mutation already
  does `qc.invalidateQueries({ queryKey: ["tasks", id] })`; add
  `qc.invalidateQueries({ queryKey: ["metrics", id] })` there and in the add-task
  flow so the UI reflects fresh metrics after task changes.
- Note: `PlanDetail` currently computes progress client-side (`completedCount`,
  `totalHours`). When wiring the metrics endpoint, prefer the server values as the
  source of truth rather than duplicating the math.

## Styling

- Use Mantine components already imported in the file (`Text`, `Group`, `Badge`,
  `Progress`, `Title`) and the existing CSS-module classes in
  `PlanDetail.module.css`. Match the dark/turquoise theme (`var(--c-turquoise)`,
  `var(--c-cool-gray)`); don't introduce a new design language.
- Keep additions inside the existing `planCard` / `planMeta` layout.

## Worked examples this skill should handle

1. **Metrics card**: `GET /plans/{id}/metrics` is fetched via TanStack Query and
   shown in the plan detail view using existing Mantine components.
2. **Live update**: toggling a task invalidates the metrics query so numbers update
   without a manual refresh.
3. **Rebalance panel**: the `GET /plans/{id}/rebalance` suggestion is rendered in
   the plan detail view, styled consistently with the existing card.
