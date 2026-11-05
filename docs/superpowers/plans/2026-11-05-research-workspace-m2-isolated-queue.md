# Research Workspace Milestone 2: Isolated Run Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace process-wide simulation state with an owner-safe, persistent, single-worker FIFO queue using isolated per-run workspaces and reproducible seeds.

**Architecture:** PostgreSQL stores the lifecycle source of truth; one in-process worker atomically claims queued rows and launches the legacy CLI in an allowlisted temporary workspace. A run-scoped process registry supports cancellation, while bounded cursor-based logs and lifecycle changes are persisted.

**Tech Stack:** Python 3.10, asyncio, SQLAlchemy 2, FastAPI, psutil, tempfile/shutil, PostgreSQL row locking, pytest.

**Spec:** `docs/superpowers/specs/2026-11-05-research-experiment-workspace-design.md`

## Global Constraints

- Exactly one simulation worker and one Uvicorn process are supported in production.
- Fixed engine ports prohibit parallel subprocess execution in this milestone.
- A workspace copies only allowlisted engine files and never copies `api/`, `.git`, `.env`, or credentials.
- Status transitions are only `queued → running|stopped` and `running → completed|failed|stopped|interrupted`.
- Terminal runs are immutable; rerun creates a new run.
- Logs retain the newest complete UTF-8 lines up to 2 MiB and expose monotonic cursors.
- Configuration, seed, engine version, and ownership are immutable once a run is queued.

## Review Focus

- Duplicate startup hooks or worker wakeups must never claim the same run twice; Task 4 tests atomic claiming.
- Cancellation racing with process completion must produce one valid terminal state; Task 4 tests both event orders.
- A crafted workspace/result filename must not escape the temporary directory; Task 2 tests the fixed allowlist and path checks.
- Log truncation between polls must report a cursor gap instead of silently losing data; Task 3 tests boundary and multibyte cases.
- Restart recovery must mark orphaned running rows interrupted and resume each queued row once; Task 4 tests repeated recovery.

---

### Task 1: Run lifecycle repository

**Files:**
- Create: `api/services/run_lifecycle.py`
- Create: `tests/api/test_run_lifecycle.py`
- Modify: `api/services/runs.py`

**Interfaces:**
- Produces: `transition_run(db, run, target_status, *, error_message=None)`, `claim_next_queued_run(db)`, `recover_runs(db)`, and `create_rerun(db, source_run, user_id)`.
- Consumes: Milestone 1 `Simulation` model and run status constants.

- [ ] **Step 1: Write failing transition, terminal-state, atomic-claim, rerun, and recovery tests**

Assert the exact allowed transition graph, `409`-equivalent domain errors for terminal stop, immutable source runs, one claim across two sessions, interrupted orphan handling, and stable queued recovery.

- [ ] **Step 2: Run focused tests and verify missing service failure**

Run: `python -m pytest tests/api/test_run_lifecycle.py -q`

Expected: FAIL because lifecycle functions do not exist.

- [ ] **Step 3: Implement lifecycle operations with row locking**

Use transactional `SELECT ... FOR UPDATE` claims on PostgreSQL and a deterministic test-safe fallback for SQLite. Store all status timestamps in UTC.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/api/test_run_lifecycle.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add api/services/run_lifecycle.py api/services/runs.py tests/api/test_run_lifecycle.py
git commit -m "feat: persist simulation run lifecycle"
```

### Task 2: Reproducible per-run workspace

**Files:**
- Create: `api/simulation/workspace.py`
- Create: `api/simulation/__init__.py`
- Create: `tests/api/test_simulation_workspace.py`
- Modify: `main.py`

**Interfaces:**
- Produces: `RunWorkspace` context manager, `build_workspace(run_id, engine_config)`, `engine_environment(run)`, `resolve_engine_version() -> str`, and `initialize_random_seed()` in `main.py`.
- Consumes: Milestone 1 `to_engine_config()` and immutable run seed.

- [ ] **Step 1: Write failing allowlist, config, cleanup, traversal, seed, and deterministic-choice tests**

Assert required modules/messages are copied, forbidden files are absent, generated config equals the engine mapping, cleanup occurs on success/failure, traversal names are rejected, and the same seed repeats representative random choices.

- [ ] **Step 2: Run focused tests and verify missing workspace failure**

Run: `python -m pytest tests/api/test_simulation_workspace.py -q`

Expected: FAIL because workspace/seed interfaces are missing.

- [ ] **Step 3: Implement the allowlisted temporary workspace and environment**

Use system-generated directories, fixed destination filenames, `FOBSIM_RUN_ID`, signed 64-bit `FOBSIM_RANDOM_SEED`, and matching `PYTHONHASHSEED`. Resolve engine version from `RENDER_GIT_COMMIT`, then application version, then `unknown`.

- [ ] **Step 4: Initialize the engine random generator before network construction**

`main.py` calls `initialize_random_seed()` before reading/creating randomized network state. Do not claim byte-identical wall-clock or crypto outputs.

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests/api/test_simulation_workspace.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add api/simulation main.py tests/api/test_simulation_workspace.py
git commit -m "feat: isolate and seed simulation workspaces"
```

### Task 3: Bounded run logs and metric extraction

**Files:**
- Create: `api/simulation/log_buffer.py`
- Create: `api/simulation/metrics.py`
- Create: `tests/api/test_log_buffer.py`
- Create: `tests/api/test_run_metrics.py`
- Modify: `api/server.py`

**Interfaces:**
- Produces: `BoundedLogBuffer(max_bytes=2_097_152)`, `append(line)`, `read_after(cursor) -> LogPage`, and `extract_run_metrics(workspace, config, cpu_readings, started_at, ended_at) -> RunMetrics`.
- Consumes: existing metric calculations from `execute_simulation` and per-run workspace output.

- [ ] **Step 1: Write failing log cursor/truncation tests**

Cover empty logs, multibyte UTF-8 boundaries, newest-line retention, monotonic cursor, and `truncated_before_cursor` after a slow client falls behind.

- [ ] **Step 2: Write failing metrics tests with fixture chain files**

Cover blocks, forks, consistency, TPS, latency, BPS, CPU, energy, missing/corrupt files, and Layer 2 calculation using the run's immutable config.

- [ ] **Step 3: Run focused tests and verify missing modules**

Run: `python -m pytest tests/api/test_log_buffer.py tests/api/test_run_metrics.py -q`

Expected: FAIL.

- [ ] **Step 4: Implement log and metric modules and remove duplicated calculation code from `server.py`**

Keep output parsing deterministic and return typed dataclasses; no database writes occur inside metric extraction.

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests/api/test_log_buffer.py tests/api/test_run_metrics.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add api/simulation/log_buffer.py api/simulation/metrics.py api/server.py tests/api/test_log_buffer.py tests/api/test_run_metrics.py
git commit -m "refactor: isolate run logs and metrics"
```

### Task 4: Single-worker queue and subprocess executor

**Files:**
- Create: `api/simulation/executor.py`
- Create: `api/simulation/queue.py`
- Create: `tests/api/test_simulation_executor.py`
- Create: `tests/api/test_simulation_queue.py`
- Modify: `api/app_factory.py`

**Interfaces:**
- Produces: `SimulationExecutor.execute(run_public_id)`, `SimulationQueue.start()`, `wake()`, `stop_run(run_public_id, user_id)`, and `shutdown()`.
- Consumes: Tasks 1–3 lifecycle, workspace, logs, and metrics interfaces.

- [ ] **Step 1: Write failing executor tests with a fake subprocess**

Assert stdin selections are correct, stdout is persisted by run, non-zero exit becomes failed, cancellation becomes stopped, metrics persist on success, errors are sanitized, and workspace cleanup always runs.

- [ ] **Step 2: Write failing queue tests**

Assert FIFO order, one active subprocess, duplicate wake/recovery cannot double-execute, queued cancellation never launches, completion/cancel races produce one valid terminal status, and shutdown marks active work interrupted.

- [ ] **Step 3: Run focused tests and verify missing implementations**

Run: `python -m pytest tests/api/test_simulation_executor.py tests/api/test_simulation_queue.py -q`

Expected: FAIL.

- [ ] **Step 4: Implement the executor and one-worker queue**

Keep the process registry private to `SimulationQueue`; key it by run UUID. Register startup/shutdown through FastAPI lifespan, not duplicate import-time tasks.

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests/api/test_simulation_executor.py tests/api/test_simulation_queue.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add api/simulation/executor.py api/simulation/queue.py api/app_factory.py tests/api/test_simulation_executor.py tests/api/test_simulation_queue.py
git commit -m "feat: add isolated simulation job queue"
```

### Task 5: Run launch, logs, stop, and rerun APIs

**Files:**
- Modify: `api/routes/runs.py`
- Modify: `api/schemas/runs.py`
- Create: `tests/api/test_run_api.py`
- Modify: `api/app_factory.py`

**Interfaces:**
- Produces: `POST /api/experiments/{id}/runs`, `GET /api/runs/{id}`, `GET /api/runs/{id}/logs`, `POST /api/runs/{id}/stop`, and `POST /api/runs/{id}/rerun`.
- Consumes: Task 4 queue and Milestone 1 owner-scoped services.

- [ ] **Step 1: Write failing API tests for lifecycle and ownership**

Cover `202` launch, generated/preserved seeds, full immutable config, owner-scoped detail/logs/stop/rerun, queued/running cancellation, terminal `409`, pagination cursor fields, and cross-user `404`.

- [ ] **Step 2: Run focused tests and verify endpoint failures**

Run: `python -m pytest tests/api/test_run_api.py -q`

Expected: FAIL.

- [ ] **Step 3: Implement thin endpoints and explicit response models**

Routes create/lookup records through services and wake/cancel through the queue. They never access subprocesses or global output directly.

- [ ] **Step 4: Run focused and full API tests**

Run: `python -m pytest tests/api -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add api/routes/runs.py api/schemas/runs.py api/app_factory.py tests/api/test_run_api.py
git commit -m "feat: expose owner-scoped run lifecycle APIs"
```

### Task 6: Compatibility adapters and global-state removal

**Files:**
- Modify: `api/server.py`
- Modify: `api/routes/runs.py`
- Create: `tests/api/test_legacy_run_adapters.py`
- Modify: `README.md`

**Interfaces:**
- Produces: temporary authenticated adapters for `/api/run`, `/api/status`, `/api/stop`, `/api/results`; removes `/ws/output` and shared config writes.
- Consumes: Task 5 run APIs/services.

- [ ] **Step 1: Write failing adapter tests**

Assert adapters require authentication, resolve only the caller's most recent active run, never expose another user's logs/results, and `POST /api/config` plus `/ws/output` are unavailable.

- [ ] **Step 2: Run focused tests and verify current global behavior fails**

Run: `python -m pytest tests/api/test_legacy_run_adapters.py -q`

Expected: FAIL because current routes use globals/shared files.

- [ ] **Step 3: Reimplement adapters over run services and delete global execution state**

Remove `simulation_running`, `simulation_output`, `simulation_process`, direct shared `Sim_parameters.json` writes, and shared `temporary` result reads from request handlers.

- [ ] **Step 4: Run milestone verification**

Run: `python -m pytest tests -q && git diff --check`

Expected: all tests pass; `rg 'simulation_running|simulation_output|simulation_process' api/server.py` returns no matches.

- [ ] **Step 5: Commit**

```bash
git add api/server.py api/routes/runs.py tests/api/test_legacy_run_adapters.py README.md
git commit -m "refactor: remove global simulation state"
```

