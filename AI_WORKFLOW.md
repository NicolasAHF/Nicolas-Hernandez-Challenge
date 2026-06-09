# AI Workflow

This repo was built with heavy use of an AI coding agent (Claude Code). Since the
challenge explicitly encourages AI use, this document explains **how** I worked with
it — the setup, the conventions, and the loop I ran for each feature — and **what I'd
change** if this were a real production project rather than a take-home.

## The setup: an agent layer before any feature code

Before writing a single line for the user stories, I built a small "agent layer" so
the AI would stay consistent with the codebase instead of re-discovering it every
session. It rests on three pieces — reusable skills, verification subagents, and
external state — and lives in the repo so it's reviewable:

- **Project memory — [`CLAUDE.md`](CLAUDE.md).** The conventions that matter: the
  strict `router → service → repository` layering, the patterns the codebase uses,
  commands, testing setup, and the working agreements below.
- **Skills — [`.claude/skills/`](.claude/skills).** Reusable, codebase-specific
  recipes the agent loads on demand:
  - `architecture-conventions` — what the codebase is (and where new code goes).
  - `backend-vertical-slice` — how to add an endpoint across the layers, tests first.
  - `redis-cache-aside` — the caching pattern (key, TTL, invalidation, fallback).
  - `frontend-plan-view` — how to surface backend data in the React/Mantine page.
- **Subagents — [`.claude/agents/`](.claude/agents).** A second opinion that didn't
  write the code: `layering-reviewer` (checks a diff against the layering/clean-code
  rules) and `acceptance-verifier` (runs the tests and checks a feature against its
  spec). Splitting authoring from verification is the single most useful structural
  habit in an AI loop.
- **State — [`docs/state/`](docs/state).** External memory so progress survives
  between sessions: `PROGRESS.md` (status of each feature) and `DECISIONS.md` (an
  ADR-lite log of trade-offs).

## Working agreements

Two rules shaped every interaction (both encoded in `CLAUDE.md`):

1. **Design decisions are reviewed before implementation.** For any non-trivial
   choice — an algorithm, a response shape, a cache TTL — the agent had to stop and
   present 2–3 concrete options with trade-offs, and I picked. This kept me in
   control of the decisions that matter and produced the `DECISIONS.md` entries as a
   by-product.
2. **One PR per feature, tests first.** Each user story was a branch off `main`, built
   red-green (write the failing test, then the code), reviewed, then opened as its own
   PR with the design rationale recorded.

## The loop I ran per feature

For each of the three user stories:

1. **Scope & decide** — the agent restated the requirement and surfaced the design
   decisions; I chose the approach.
2. **TDD** — failing tests through the HTTP layer first, then the implementation in
   the service, keeping the router/repository thin.
3. **Verify** — full test suite green, then a review pass for layering/clean-code.
4. **Document & ship** — record the decision in `DECISIONS.md`, update `PROGRESS.md`,
   open the PR.

The human judgment mattered most at step 1. The clearest example: for *plan
rebalancing*, the agent's first proposal was to scale every task's hours down
proportionally. I rejected it — a task that genuinely needs 12 hours can't be "done
in 6" — and we pivoted to redistributing whole tasks across weeks (splitting only
tasks larger than the weekly budget). That decision, not the code, was the real work,
and it's exactly the kind of call the "decide before implementing" rule exists to
force.

## What I'd change for a real production project

These are about scaling the AI workflow itself rather than the feature code:

- **Take task context from the issue tracker, not from in-repo state files.** Here I
  used `docs/state/` because the project is small and there's no task-tracking tool.
  On a real team I'd pull the work item straight from whatever tracker the company
  uses — Jira through the **Atlassian MCP**, or another tool (Linear, Azure Boards, …)
  through its own MCP — so the agent reads the ticket and builds its context from
  there instead of from files I maintain by hand. I'd also be cautious about adding
  context files in a
  large codebase: each one is another artifact to keep in sync with the code, so on
  top of maintaining the code you end up maintaining its documentation layer too —
  and stale context misleads an agent the same way stale comments mislead a human. The
  overhead has to clearly earn its keep.

- **Move the skills and subagents into a shared, installable toolkit.** They live in
  this repo, but ideally they'd sit in a dedicated repository (skills, subagents,
  hooks, commands) that can be installed into any project, so every codebase the
  company works on gets consistent results from the same building blocks. Genuinely
  project-specific pieces — tied to a particular stack or local practice — would layer
  on top of that shared base. For the skills and subagents I wrote here, I
  deliberately adapted them to the conventions already established in this project
  rather than imposing a generic style.

- **Add more MCPs for the things an agent shouldn't do blind.** Browser-driving MCPs
  like **Playwright** or **Chrome DevTools** would let the agent validate UI changes
  and debug directly in the browser instead of reasoning about the DOM in the dark —
  used, of course, only if the company has approved those tools.
