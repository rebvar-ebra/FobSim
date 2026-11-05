# Research Workspace Milestone 3: Research Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single simulation flow with Projects, Experiment Editor, Run Detail, and owner-safe history navigation while preserving the existing visual language.

**Architecture:** A typed frontend API layer owns authenticated requests and errors. New App Router pages compose focused project, experiment, and run components; the existing function/consensus/parameter controls are reused rather than duplicated.

**Tech Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, Vitest, Testing Library, existing Lucide/Recharts components.

**Spec:** `docs/superpowers/specs/2026-11-05-research-experiment-workspace-design.md`

## Global Constraints

- All research pages require authentication and preserve a return URL through login.
- UI resource identifiers are UUID strings; integer database IDs are never exposed.
- Existing visual tokens/components are reused; no second design system is introduced.
- A run's config, seed, and engine version are displayed as immutable values.
- Polling stops on unmount and on every terminal run state.
- Legacy runs clearly label missing seed/log/results instead of fabricating data.
- The existing dashboard remains usable during route-by-route migration.

## Review Focus

- Expired/missing tokens during polling must redirect once without an infinite request loop; Task 1 and Task 4 test this.
- Empty projects, archived experiments, failed runs, and legacy partial runs need explicit useful states; Tasks 2–5 test them.
- Rapid navigation between runs must not leak the previous run's logs; Task 4 tests abort/cleanup behavior.
- Long names, hypotheses, logs, and mobile layouts must not break actions or hide status; component tests use long content in Tasks 2–4.
- Launch/stop/rerun double-clicks must not create duplicate requests; Tasks 3 and 4 test disabled pending states.

---

### Task 1: Typed authenticated API client

**Files:**
- Create: `frontend/src/lib/api/client.ts`
- Create: `frontend/src/lib/api/types.ts`
- Create: `frontend/src/lib/api/projects.ts`
- Create: `frontend/src/lib/api/experiments.ts`
- Create: `frontend/src/lib/api/runs.ts`
- Create: `frontend/src/lib/api/client.test.ts`
- Modify: `frontend/src/app/api.ts`

**Interfaces:**
- Produces: `apiFetch<T>()`, `ApiError`, resource types, and typed project/experiment/run functions.
- Consumes: existing `API_URL` and localStorage bearer token behavior.

- [ ] **Step 1: Write failing tests for auth headers, JSON/error parsing, 401 handling, and abort signals**

Assert one bearer header, typed successful data, safe error messages, one login redirect with encoded return path, and forwarded `AbortSignal`.

- [ ] **Step 2: Run focused tests and verify module failures**

Run: `npm test -- src/lib/api/client.test.ts`

Expected: FAIL because the client modules do not exist.

- [ ] **Step 3: Implement the minimal typed client and resource functions**

Centralize token and error behavior. Do not repeat raw `fetch` logic in pages.

- [ ] **Step 4: Run focused tests**

Run: `npm test -- src/lib/api/client.test.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/api frontend/src/app/api.ts
git commit -m "feat: add typed research API client"
```

### Task 2: Projects dashboard and project detail

**Files:**
- Create: `frontend/src/app/projects/page.tsx`
- Create: `frontend/src/app/projects/[projectId]/page.tsx`
- Create: `frontend/src/app/projects/components/ProjectCard.tsx`
- Create: `frontend/src/app/projects/components/ProjectForm.tsx`
- Create: `frontend/src/app/projects/page.test.tsx`
- Create: `frontend/src/app/projects/[projectId]/page.test.tsx`
- Modify: `frontend/src/app/components/Sidebar.tsx`
- Modify: `frontend/src/app/page.tsx`

**Interfaces:**
- Produces: project list/create/edit/soft-delete UI and project detail experiment list.
- Consumes: Task 1 project/experiment API functions and existing `RequireAuth`.

- [ ] **Step 1: Write failing list/create/empty/error/long-name/mobile-safe component tests**

Assert project cards show counts/latest run, empty state starts creation, validation matches backend bounds, pending submission cannot duplicate, and foreign/missing project errors provide safe navigation.

- [ ] **Step 2: Run focused tests and verify route/component failures**

Run: `npm test -- src/app/projects/page.test.tsx src/app/projects/[projectId]/page.test.tsx`

Expected: FAIL.

- [ ] **Step 3: Implement project pages and focused components**

Add Projects to the sidebar and make the authenticated dashboard's primary action open `/projects`. Preserve current styling and responsive behavior.

- [ ] **Step 4: Run focused tests**

Run: `npm test -- src/app/projects/page.test.tsx src/app/projects/[projectId]/page.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/projects frontend/src/app/components/Sidebar.tsx frontend/src/app/page.tsx
git commit -m "feat: add research project workspace"
```

### Task 3: Experiment editor and run launch

**Files:**
- Create: `frontend/src/app/projects/[projectId]/experiments/new/page.tsx`
- Create: `frontend/src/app/experiments/[experimentId]/page.tsx`
- Create: `frontend/src/app/experiments/components/ExperimentIdentityStep.tsx`
- Create: `frontend/src/app/experiments/components/ExperimentEditor.tsx`
- Create: `frontend/src/app/experiments/components/ExperimentEditor.test.tsx`
- Modify: `frontend/src/app/simulate/components/FunctionSelector.tsx`
- Modify: `frontend/src/app/simulate/components/ConsensusSelector.tsx`
- Modify: `frontend/src/app/simulate/components/ParameterConfig.tsx`
- Modify: `frontend/src/app/simulate/constants.tsx`

**Interfaces:**
- Produces: create/edit/clone experiment flow and `Run experiment` launch navigation.
- Consumes: Task 1 experiment/run APIs and existing selector components as controlled inputs.

- [ ] **Step 1: Write failing editor tests**

Cover identity/hypothesis, complete configuration, server validation errors, Fog-vs-End-User dependent validation, generated/default seed display, save, clone, launch, and duplicate-click prevention.

- [ ] **Step 2: Run focused tests and verify missing editor failure**

Run: `npm test -- src/app/experiments/components/ExperimentEditor.test.tsx`

Expected: FAIL.

- [ ] **Step 3: Refactor existing selectors into reusable controlled components**

Preserve visual output and current `/simulate` compatibility. Move duplicated option metadata into typed constants.

- [ ] **Step 4: Implement experiment pages and editor flow**

Saving updates the template; launching calls the run endpoint once and navigates to `/runs/{runId}`.

- [ ] **Step 5: Run focused and existing simulation/auth tests**

Run: `npm test -- src/app/experiments/components/ExperimentEditor.test.tsx src/app/components/RequireAuth.test.tsx src/app/auth/login/page.test.tsx`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/projects/[projectId]/experiments frontend/src/app/experiments frontend/src/app/simulate/components frontend/src/app/simulate/constants.tsx
git commit -m "feat: add reusable experiment editor"
```

### Task 4: Run detail, live logs, stop, and rerun

**Files:**
- Create: `frontend/src/app/runs/[runId]/page.tsx`
- Create: `frontend/src/app/runs/components/RunStatus.tsx`
- Create: `frontend/src/app/runs/components/RunLog.tsx`
- Create: `frontend/src/app/runs/components/RunMetrics.tsx`
- Create: `frontend/src/app/runs/components/RunConfiguration.tsx`
- Create: `frontend/src/app/runs/[runId]/page.test.tsx`
- Create: `frontend/src/hooks/useRunPolling.ts`
- Create: `frontend/src/hooks/useRunPolling.test.tsx`

**Interfaces:**
- Produces: run detail page and `useRunPolling(runId)` with cursor-based log polling and cleanup.
- Consumes: Task 1 run APIs and Milestone 2 lifecycle/log response types.

- [ ] **Step 1: Write failing polling tests**

Cover queued/running/terminal states, cursor advancement, truncation warning, abort on navigation, 401 redirect once, failed requests with retry, and no stale logs after run ID changes.

- [ ] **Step 2: Write failing run-page tests**

Cover immutable seed/version/config, metric units, queued stop, running stop, failed/interrupted states, legacy partial state, rerun navigation, and pending-action double-click prevention.

- [ ] **Step 3: Run focused tests and verify missing hook/page failures**

Run: `npm test -- src/hooks/useRunPolling.test.tsx src/app/runs/[runId]/page.test.tsx`

Expected: FAIL.

- [ ] **Step 4: Implement polling hook and focused run components**

Poll status/logs only while non-terminal. Preserve a visible truncation notice when `truncated_before_cursor` advances.

- [ ] **Step 5: Run focused tests**

Run: `npm test -- src/hooks/useRunPolling.test.tsx src/app/runs/[runId]/page.test.tsx`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/runs frontend/src/hooks
git commit -m "feat: add live research run details"
```

### Task 5: History and dashboard migration

**Files:**
- Modify: `frontend/src/app/results/page.tsx`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/components/Sidebar.tsx`
- Create: `frontend/src/app/results/page.test.tsx`
- Modify: `frontend/src/app/simulate/page.tsx`

**Interfaces:**
- Produces: UUID-linked history, project-aware dashboard summaries, and compatibility redirect from `/simulate` to experiment creation.
- Consumes: Tasks 1–4 pages and APIs.

- [ ] **Step 1: Write failing history/dashboard tests**

Assert completed/failed/interrupted/legacy rows render accurately, filters work, ExternalLink reaches `/runs/{uuid}`, pagination loads more, and empty history points to Projects.

- [ ] **Step 2: Run focused tests and verify current inert action fails**

Run: `npm test -- src/app/results/page.test.tsx`

Expected: FAIL because the action button has no run link and data is untyped.

- [ ] **Step 3: Migrate history/dashboard and provide `/simulate` compatibility**

Keep `/simulate` protected but redirect researchers to select/create a project experiment instead of using global configuration.

- [ ] **Step 4: Run all frontend tests and build**

Run: `npm test && npm run lint && npm run build`

Expected: all tests pass, lint has no errors, build exits 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/results frontend/src/app/page.tsx frontend/src/app/components/Sidebar.tsx frontend/src/app/simulate/page.tsx
git commit -m "feat: connect history to research runs"
```

