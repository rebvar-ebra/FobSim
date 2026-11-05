# Research Workspace Milestone 4: Exports and Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist bounded structured artifacts, provide trustworthy JSON/CSV/ZIP reproducibility exports, migrate analytics, remove compatibility/global surfaces, and verify production readiness.

**Architecture:** A versioned artifact schema captures only public research outputs. An export service generates deterministic entries and checksums on demand; analytics reads completed immutable runs. Final cleanup removes legacy global endpoints and hardens deployment/documentation.

**Tech Stack:** Python 3.10, FastAPI StreamingResponse, csv/json/zipfile/hashlib, SQLAlchemy 2, Next.js 16, Recharts, pytest, Vitest.

**Spec:** `docs/superpowers/specs/2026-11-05-research-experiment-workspace-design.md`

## Global Constraints

- Persisted logs are capped at 2 MiB and structured results at 5 MiB during capture.
- Private keys, credentials, `.env` content, password data, and arbitrary temporary files are never persisted or exported.
- ZIP entries have fixed server-defined names and SHA-256 checksums over their final bytes.
- JSON/CSV/ZIP exports are available only to the run owner; legacy partial runs never imply unavailable completeness.
- Analytics includes only the authenticated user's `completed` runs.
- PDF, object storage, collaboration, batch sweeps, and advanced statistics remain out of scope.

## Review Focus

- Malicious filenames, zip-slip paths, huge results, and secret-like temporary files must never enter exports; Tasks 1–2 test them.
- CSV formula injection in textual values must be neutralized and units remain explicit; Task 2 tests spreadsheet-dangerous prefixes.
- Legacy or truncated runs must generate honest partial metadata or a clear unavailable response; Tasks 1–3 test both paths.
- Analytics with zero completed runs, null legacy metrics, and mixed owners must remain stable; Task 4 tests all three.
- Removing compatibility endpoints must not leave frontend or documentation references behind; Task 5 verifies with repository searches and end-to-end tests.

---

### Task 1: Versioned artifact capture and persistence

**Files:**
- Create: `api/artifacts/schema.py`
- Create: `api/artifacts/capture.py`
- Create: `api/artifacts/store.py`
- Create: `api/artifacts/__init__.py`
- Create: `tests/api/test_artifact_capture.py`
- Modify: `api/simulation/executor.py`
- Modify: `api/schemas/runs.py`

**Interfaces:**
- Produces: `RunResultsV1`, `ArtifactManifestV1`, `ArtifactStore` protocol, `PostgresArtifactStore`, `capture_results(workspace, limits)`, and explicit truncation/availability fields.
- Consumes: Milestone 2 per-run workspace and `Simulation.results_json`/manifest fields.

- [ ] **Step 1: Write failing schema, limit, corruption, and secret-exclusion tests**

Cover valid blocks/stakes/burned summaries, corrupt/missing files, deterministic ordering, 5 MiB cutoff during reading, truncation flags, forbidden private-key/env files, fixed public result categories, and storage round-trips through the protocol.

- [ ] **Step 2: Run focused tests and verify missing artifact modules**

Run: `python -m pytest tests/api/test_artifact_capture.py -q`

Expected: FAIL.

- [ ] **Step 3: Implement versioned schemas and bounded streaming capture**

Never enumerate arbitrary files into persisted results. Read only fixed known output filenames/patterns and public fields. Keep capture independent from storage so a later S3-compatible implementation can replace `PostgresArtifactStore` without changing executor or API contracts.

- [ ] **Step 4: Integrate capture before workspace cleanup**

Completed and failed runs retain bounded available evidence; manifest flags explain missing/corrupt/truncated categories.

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests/api/test_artifact_capture.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add api/artifacts api/simulation/executor.py api/schemas/runs.py tests/api/test_artifact_capture.py
git commit -m "feat: persist bounded research artifacts"
```

### Task 2: JSON, CSV, and ZIP export service

**Files:**
- Create: `api/services/exports.py`
- Create: `tests/api/test_exports.py`
- Modify: `api/routes/runs.py`
- Modify: `api/schemas/runs.py`

**Interfaces:**
- Produces: `build_json_export(run)`, `build_metrics_csv(run)`, `build_reproducibility_zip(run)`, and `GET /api/runs/{id}/export?format=json|csv|zip`.
- Consumes: Task 1 versioned results/manifest and owner-scoped run service.

- [ ] **Step 1: Write failing export-content, checksum, ownership, and safety tests**

Assert exact ZIP names, manifest schema version, config/seed/engine/timestamps, documented metric units, checksum match over final bytes, no path traversal, formula-safe CSV cells, owner-only access, and clear legacy/truncation metadata.

- [ ] **Step 2: Run focused tests and verify missing service/route failures**

Run: `python -m pytest tests/api/test_exports.py -q`

Expected: FAIL.

- [ ] **Step 3: Implement deterministic in-memory JSON/CSV entries and streamed ZIP response**

Use fixed filenames: `manifest.json`, `config.json`, `metrics.csv`, `logs.txt`, `results.json`, `README.txt`. Sort JSON keys and stabilize newlines.

- [ ] **Step 4: Implement owner-scoped export endpoint and content headers**

Return `404` for foreign runs, `422` for unsupported format, and safe UUID-based download filenames.

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests/api/test_exports.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add api/services/exports.py api/routes/runs.py api/schemas/runs.py tests/api/test_exports.py
git commit -m "feat: export reproducible research bundles"
```

### Task 3: Export controls and legacy disclosure UI

**Files:**
- Create: `frontend/src/app/runs/components/ExportMenu.tsx`
- Create: `frontend/src/app/runs/components/ExportMenu.test.tsx`
- Modify: `frontend/src/app/runs/[runId]/page.tsx`
- Modify: `frontend/src/lib/api/runs.ts`
- Modify: `frontend/src/lib/api/types.ts`

**Interfaces:**
- Produces: authenticated JSON/CSV/ZIP download controls and partial/truncated artifact disclosures.
- Consumes: Task 2 export endpoint and run availability fields.

- [ ] **Step 1: Write failing export UI tests**

Cover each format, authenticated blob download, pending state, server error, unavailable legacy artifacts, truncation warning, and safe UUID filename.

- [ ] **Step 2: Run focused tests and verify missing component failure**

Run: `npm test -- src/app/runs/components/ExportMenu.test.tsx`

Expected: FAIL.

- [ ] **Step 3: Implement typed download API and accessible export menu**

Disable unavailable formats with an explanation; do not hide why a legacy or truncated artifact differs.

- [ ] **Step 4: Run focused tests**

Run: `npm test -- src/app/runs/components/ExportMenu.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/runs frontend/src/lib/api
git commit -m "feat: add research export controls"
```

### Task 4: Immutable-run analytics migration

**Files:**
- Create: `api/services/analytics.py`
- Create: `tests/api/test_analytics.py`
- Modify: `api/server.py`
- Modify: `frontend/src/app/analytics/page.tsx`
- Create: `frontend/src/app/analytics/page.test.tsx`

**Interfaces:**
- Produces: owner-scoped completed-run aggregation with typed metrics and stable empty/null behavior.
- Consumes: immutable `Simulation` records and existing Recharts UI.

- [ ] **Step 1: Write failing backend analytics tests**

Assert only completed owner runs count, other owners and failed/legacy-null metrics are excluded or handled, zero data returns an empty list, and units/rounding remain explicit.

- [ ] **Step 2: Implement analytics service and thin route**

Move aggregation out of `server.py`; retain endpoint compatibility while returning an explicit response schema.

- [ ] **Step 3: Write failing frontend empty/data/error tests**

Assert charts use typed values, zero data shows a research-oriented empty state, and auth/API failures do not render misleading zero metrics.

- [ ] **Step 4: Update analytics page and run focused tests**

Run: `python -m pytest tests/api/test_analytics.py -q && npm test -- src/app/analytics/page.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add api/services/analytics.py api/server.py tests/api/test_analytics.py frontend/src/app/analytics
git commit -m "refactor: analyze immutable research runs"
```

### Task 5: Remove compatibility surfaces and harden documentation

**Files:**
- Modify: `api/server.py`
- Modify: `api/app_factory.py`
- Modify: `frontend/src/app/simulate/page.tsx`
- Modify: `README.md`
- Modify: `render.yaml`
- Create: `docs/research-workflow.md`
- Create: `tests/api/test_removed_legacy_endpoints.py`

**Interfaces:**
- Produces: final research API surface, deployment documentation, reproduction instructions, and no global execution endpoints.
- Consumes: all previous milestones.

- [ ] **Step 1: Write failing endpoint-removal tests**

Assert old `/api/run`, `/api/status`, `/api/stop`, `/api/results`, `POST /api/config`, and `/ws/output` are unavailable while new project/experiment/run routes remain healthy.

- [ ] **Step 2: Remove compatibility handlers and stale frontend references**

Delete old global endpoint code after confirming the new UI uses no adapter. Keep `GET /api/config` only for authenticated canonical defaults if still used by the editor.

- [ ] **Step 3: Update research/deployment documentation**

Document project→experiment→run workflow, seed semantics, status meanings, export contents/limits, legacy partial data, single-worker/port limitation, migrations, required Render variables, and FobSim citation.

- [ ] **Step 4: Verify no stale references remain**

Run: `rg -n '/api/(run|status|stop|results)|ws/output|simulation_running|simulation_output|simulation_process' api frontend/src README.md docs -g '!docs/superpowers/**'`

Expected: no executable stale references; documentation may mention removed endpoints only in migration notes.

- [ ] **Step 5: Run full repository verification**

Run: `python -m pytest tests -q && cd frontend && npm test && npm run lint && npm run build && cd .. && git diff --check`

Expected: all backend/frontend tests pass, lint has no errors, production build exits 0, and diff check is clean.

- [ ] **Step 6: Build the production backend image**

Run: `docker build -f api/Dockerfile -t fobsim-backend:research-workspace .`

Expected: image builds and migration-first entrypoint is present.

- [ ] **Step 7: Commit**

```bash
git add api frontend/src README.md render.yaml docs/research-workflow.md tests/api/test_removed_legacy_endpoints.py
git commit -m "feat: complete reproducible research workflow"
```

### Task 6: Production migration and end-to-end verification

**Files:**
- Create: `docs/deployment/research-workspace-checklist.md`
- Modify: `README.md`

**Interfaces:**
- Produces: a reversible deployment checklist and recorded smoke-test evidence.
- Consumes: production Render services and all milestone acceptance criteria.

- [ ] **Step 1: Write the pre-deploy and rollback checklist**

Include database backup, required env vars, current commit, migration command, health checks, rollback image/commit, and the rule that schema rollback must not delete research rows.

- [ ] **Step 2: Deploy backend and verify migration before frontend activation**

Confirm Alembic head, health endpoint, existing login/history, and legacy partial run detail before exposing new frontend routes.

- [ ] **Step 3: Deploy frontend and execute the two-user isolation smoke test**

Create two test users/projects/experiments; queue different configs; verify each sees only its own run/logs/exports and cannot stop or fetch the other's UUID.

- [ ] **Step 4: Execute reproducibility and restart smoke tests**

Rerun one config/seed, compare seeded choices, restart with one queued and one controlled active run, verify queued resumes once and active becomes interrupted.

- [ ] **Step 5: Execute export integrity smoke tests**

Download JSON/CSV/ZIP, verify documented files/units/checksums, and confirm no credential/private-key material appears.

- [ ] **Step 6: Record results and commit the finalized checklist**

```bash
git add docs/deployment/research-workspace-checklist.md README.md
git commit -m "docs: verify research workspace deployment"
```

