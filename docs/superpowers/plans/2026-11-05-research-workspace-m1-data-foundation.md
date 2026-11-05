# Research Workspace Milestone 1: Data Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce safe database migrations, canonical experiment configuration, owner-scoped projects/experiments, and paginated run history without changing the existing simulation UI.

**Architecture:** Keep the current FastAPI application online while adding Alembic-managed schema changes and focused route/service modules. Existing simulations remain readable with nullable experiment relationships; new project and experiment APIs are owner-scoped and use explicit Pydantic schemas.

**Tech Stack:** Python 3.10, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL, pytest/httpx, existing JWT authentication.

**Spec:** `docs/superpowers/specs/2026-11-05-research-experiment-workspace-design.md`

## Global Constraints

- Preserve every existing user and simulation row; no destructive migration is allowed.
- Public resource identifiers are server-generated UUIDs and timestamps are timezone-aware UTC.
- Every project, experiment, and run query is scoped to the authenticated user's integer `User.id`.
- Canonical configuration contains the complete effective `Sim_parameters.json` schema and centrally maps legacy question-mark keys.
- PostgreSQL is the production store; tests use SQLite only where behavior is database-independent.
- Production startup runs `alembic upgrade head` before starting one Uvicorn worker.
- Do not write project secrets, database URLs, JWT secrets, or Resend keys to source control.

## Review Focus

- A database created before Alembic must upgrade in place without losing users or simulations; Task 2 pins this with a legacy-schema migration test.
- A user guessing another user's UUID must receive `404`, not data or an existence leak; Task 5 tests cross-user access on every resource type.
- Legacy and question-mark-suffixed config keys must round-trip to one canonical snapshot; Task 3 tests all aliases.
- Fog placement must validate Byzantine/delegate/neighbour counts against fog nodes, not `NumOfMiners`; Task 3 tests both placements.
- Empty, very long, duplicate, archived, and paginated project/experiment inputs must remain predictable; Task 5 tests bounds, archives, and cursor behavior.

---

### Task 1: Backend test harness and application factory

**Files:**
- Create: `api/requirements-dev.txt`
- Create: `api/app_factory.py`
- Create: `tests/api/conftest.py`
- Create: `tests/api/test_app_factory.py`
- Modify: `api/server.py`

**Interfaces:**
- Produces: `create_app() -> FastAPI` in `api/app_factory.py` and pytest fixtures `db_session`, `client`, `user_factory`, `auth_headers`.
- Consumes: existing `database.Base`, `database.get_db`, and authentication dependency.

- [ ] **Step 1: Write failing factory and dependency-override tests**

Add tests named `test_create_app_registers_health_and_auth_routes` and `test_client_uses_isolated_database`, asserting `/` returns 200 and data created in one test database is absent from a fresh fixture.

- [ ] **Step 2: Run the focused tests and verify the expected import/factory failure**

Run: `python -m pytest tests/api/test_app_factory.py -q`

Expected: FAIL because `api.app_factory.create_app` and fixtures do not exist.

- [ ] **Step 3: Add development dependencies and implement the minimal app factory**

`api/requirements-dev.txt` includes `-r requirements.txt`, `pytest>=8.0`, `pytest-asyncio>=0.23`, and `httpx>=0.27`. Move FastAPI construction and router registration behind `create_app()`, while keeping `api/server.py` as the current executable entry point.

- [ ] **Step 4: Run focused and existing backend tests**

Run: `python -m pytest tests/api/test_app_factory.py tests/test_email_service.py tests/test_password_reset_tokens.py tests/test_password_reset_api.py -q`

Expected: PASS with no production database access.

- [ ] **Step 5: Commit**

```bash
git add api/requirements-dev.txt api/app_factory.py api/server.py tests/api/conftest.py tests/api/test_app_factory.py
git commit -m "test: add isolated FastAPI test harness"
```

### Task 2: Alembic baseline and legacy-safe schema migration

**Files:**
- Create: `api/alembic.ini`
- Create: `api/migrations/env.py`
- Create: `api/migrations/script.py.mako`
- Create: `api/migrations/versions/20261105_01_research_workspace.py`
- Create: `tests/api/test_migrations.py`
- Modify: `api/models.py`
- Modify: `api/requirements.txt`

**Interfaces:**
- Produces: models `ResearchProject`, `Experiment`, extended `Simulation`, and Alembic head revision `20261105_01`.
- Consumes: existing `User`, `Simulation`, and `PasswordResetToken` tables.

- [ ] **Step 1: Write migration tests against empty and legacy schemas**

Add `test_upgrade_empty_database_to_head` and `test_upgrade_legacy_database_preserves_rows_and_backfills_public_ids`. The legacy test creates the current tables manually, inserts one user and one `running` simulation, upgrades, then asserts the rows remain, `public_id` is non-null/unique, and status is `interrupted`.

- [ ] **Step 2: Run migration tests and verify they fail without Alembic configuration**

Run: `python -m pytest tests/api/test_migrations.py -q`

Expected: FAIL because Alembic and revision files are missing.

- [ ] **Step 3: Add Alembic and extend the SQLAlchemy models**

Use SQLAlchemy `Uuid(as_uuid=True)`. `ResearchProject.id` and `Experiment.id` are UUID primary keys. Keep legacy integer primary keys on `users` and `simulations` internally; add/expose `Simulation.public_id` as the run UUID. Add the relationships and remaining run fields from the spec.

- [ ] **Step 4: Implement the inspection-based initial migration**

The revision creates absent tables, adds absent columns to existing tables, backfills UUIDs, maps known legacy statuses, marks legacy `running` rows `interrupted`, and creates indexes/foreign keys without recreating populated tables.

- [ ] **Step 5: Run migration tests twice to prove idempotent head behavior**

Run: `python -m pytest tests/api/test_migrations.py -q && python -m pytest tests/api/test_migrations.py -q`

Expected: PASS both times.

- [ ] **Step 6: Commit**

```bash
git add api/alembic.ini api/migrations api/models.py api/requirements.txt tests/api/test_migrations.py
git commit -m "feat: add legacy-safe research schema migrations"
```

### Task 3: Canonical simulation configuration

**Files:**
- Create: `api/config_schema.py`
- Create: `tests/api/test_config_schema.py`
- Modify: `api/server.py`

**Interfaces:**
- Produces: `SimulationConfig`, `canonicalize_config(raw: Mapping[str, Any]) -> dict[str, Any]`, `to_engine_config(config: SimulationConfig) -> dict[str, Any]`, and `effective_miner_count(config, placement) -> int`.
- Consumes: current `Sim_parameters.json` keys and the function/placement/consensus identifiers in `api/server.py`.

- [ ] **Step 1: Write failing alias, complete-snapshot, bounds, and placement-aware tests**

Tests assert question-mark keys and API field names produce the same canonical model; defaults fill every engine key; Fog uses `NumOfFogNodes`; End User uses `NumOfMiners`; excessive Byzantine nodes, neighbours, and DPoS delegates raise validation errors.

- [ ] **Step 2: Run focused tests and verify missing-module failure**

Run: `python -m pytest tests/api/test_config_schema.py -q`

Expected: FAIL because `api.config_schema` does not exist.

- [ ] **Step 3: Implement the canonical Pydantic model and explicit engine mapping**

Use typed fields, exact safe bounds, and one `LEGACY_ENGINE_KEYS` mapping. Do not scatter aliases across routes. Keep the persisted canonical JSON free of punctuation-dependent legacy names.

- [ ] **Step 4: Replace the duplicate `SimConfig` in `api/server.py`**

Compatibility routes consume `SimulationConfig`; file output uses only `to_engine_config()`.

- [ ] **Step 5: Run configuration and existing API tests**

Run: `python -m pytest tests/api/test_config_schema.py tests/test_password_reset_api.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add api/config_schema.py api/server.py tests/api/test_config_schema.py
git commit -m "feat: canonicalize simulation configuration"
```

### Task 4: Explicit API schemas and owner-scoped services

**Files:**
- Create: `api/schemas/__init__.py`
- Create: `api/schemas/projects.py`
- Create: `api/schemas/experiments.py`
- Create: `api/schemas/runs.py`
- Create: `api/services/__init__.py`
- Create: `api/services/projects.py`
- Create: `api/services/experiments.py`
- Create: `api/services/runs.py`
- Create: `tests/api/test_owner_services.py`

**Interfaces:**
- Produces: `get_owned_project`, `get_owned_experiment`, `get_owned_run`, project/experiment CRUD functions, `list_owned_runs`, and typed request/response schemas.
- Consumes: Task 2 models and Task 3 `SimulationConfig`.

- [ ] **Step 1: Write failing service tests for ownership, archives, immutable run snapshots, and pagination**

Tests create two users and assert owner queries succeed, cross-user UUIDs return `None`, archived records are hidden from normal lists, existing runs retain old config after experiment edits, and cursor/limit ordering is stable.

- [ ] **Step 2: Run focused tests and verify service imports fail**

Run: `python -m pytest tests/api/test_owner_services.py -q`

Expected: FAIL because service modules are missing.

- [ ] **Step 3: Implement explicit schemas and minimal service functions**

Use UUIDs in public schemas, integer IDs only internally, UTC timestamps, and service-level owner filters on every lookup. Define run status constants in `api/services/runs.py`; do not introduce a PostgreSQL enum.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/api/test_owner_services.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add api/schemas api/services tests/api/test_owner_services.py
git commit -m "feat: add owner-scoped research services"
```

### Task 5: Project, experiment, and paginated run APIs

**Files:**
- Create: `api/routes/__init__.py`
- Create: `api/routes/projects.py`
- Create: `api/routes/experiments.py`
- Create: `api/routes/runs.py`
- Create: `tests/api/test_research_api.py`
- Modify: `api/app_factory.py`
- Modify: `api/server.py`

**Interfaces:**
- Produces: the project/experiment endpoints and `GET /api/runs`; `/api/simulations` becomes an authenticated compatibility adapter.
- Consumes: Task 4 schemas/services and existing `auth.get_current_user`.

- [ ] **Step 1: Write failing end-to-end API tests**

Cover create/list/get/update/soft-delete projects; create/list/get/update/archive/clone experiments; paginated run listing; field-length validation; duplicate names allowed across projects; and `404` for every cross-user UUID request.

- [ ] **Step 2: Run focused tests and verify route failures**

Run: `python -m pytest tests/api/test_research_api.py -q`

Expected: FAIL with 404 for the new endpoints.

- [ ] **Step 3: Implement thin routers that delegate to owner-scoped services**

Return `201` on create, `204` on soft delete/archive, `404` for missing or foreign-owned resources, and `409` when deleting a project with queued/running runs.

- [ ] **Step 4: Convert `/api/simulations` to the compatibility adapter**

Keep its existing response shape for the current frontend while sourcing rows from `list_owned_runs`; require authentication and never include another user's run.

- [ ] **Step 5: Run API and full backend tests**

Run: `python -m pytest tests/api tests/test_email_service.py tests/test_password_reset_tokens.py tests/test_password_reset_api.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add api/routes api/app_factory.py api/server.py tests/api/test_research_api.py
git commit -m "feat: expose research project and experiment APIs"
```

### Task 6: Production migration entrypoint and security configuration

**Files:**
- Create: `api/entrypoint.sh`
- Create: `tests/api/test_runtime_config.py`
- Modify: `api/auth.py`
- Modify: `api/app_factory.py`
- Modify: `api/Dockerfile`
- Modify: `render.yaml`
- Modify: `README.md`

**Interfaces:**
- Produces: migration-before-start container entrypoint, `JWT_SECRET_KEY` runtime configuration, and exact-origin CORS via `FRONTEND_URL`.
- Consumes: Task 2 Alembic configuration and existing Render deployment.

- [ ] **Step 1: Write failing tests for production secret and CORS configuration**

Tests assert production mode rejects a missing/placeholder JWT secret, configured `FRONTEND_URL` is the only allowed credentialed origin, and development mode can use an explicit development secret.

- [ ] **Step 2: Run focused tests and verify current hard-coded-secret behavior fails them**

Run: `python -m pytest tests/api/test_runtime_config.py -q`

Expected: FAIL because `api/auth.py` hard-codes the secret and CORS allows `*`.

- [ ] **Step 3: Implement environment-based JWT and CORS configuration**

Require `JWT_SECRET_KEY` in production. Read `FRONTEND_URL` as the single production origin. Keep secrets out of logs and response bodies.

- [ ] **Step 4: Add migration-first entrypoint and Render declarations**

`api/entrypoint.sh` runs `alembic -c api/alembic.ini upgrade head` and then `exec python3 api/server.py`. `render.yaml` declares `JWT_SECRET_KEY`, `RESEND_API_KEY`, and `RESEND_FROM_EMAIL` with `sync: false`; `FRONTEND_URL` is the non-secret value `https://fobsim-frontend.onrender.com`. It never contains secret values.

- [ ] **Step 5: Build and smoke-test the backend container**

Run: `docker build -f api/Dockerfile -t fobsim-backend:m1 .`

Expected: image builds successfully and entrypoint is executable.

- [ ] **Step 6: Run the full milestone verification**

Run: `python -m pytest tests -q && git diff --check`

Expected: all tests pass and no whitespace errors.

- [ ] **Step 7: Commit**

```bash
git add api/entrypoint.sh api/auth.py api/app_factory.py api/Dockerfile render.yaml README.md tests/api/test_runtime_config.py
git commit -m "chore: migrate and secure backend startup"
```

