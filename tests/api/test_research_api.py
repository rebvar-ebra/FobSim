"""Research HTTP contracts exercised against the real database and authentication."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import update

import auth
import models
from api.schemas.projects import ProjectCreate
from api.schemas.experiments import ExperimentCreate
from api.services.projects import create_project
from api.services.experiments import create_experiment


EXPERIMENT = {
    "name": "Baseline", "blockchain_function": 1,
    "blockchain_placement": 1, "consensus_algorithm": 1,
    "config": {}, "default_seed": 42,
}


@pytest.fixture
def workspace(db_session, user_factory):
    owner, stranger = user_factory(), user_factory()
    project = create_project(db_session, owner.id, ProjectCreate(name="Study"))
    experiment = create_experiment(
        db_session, owner.id, project.id, ExperimentCreate(**EXPERIMENT),
    )
    run = models.Simulation(user_id=owner.id, experiment_id=experiment.id,
                            status="completed", config={"legacy": 3})
    db_session.add(run)
    db_session.commit()

    def headers(user):
        return {"Authorization": f"Bearer {auth.create_access_token({'sub': user.email})}"}

    return owner, stranger, project, experiment, run, headers(owner), headers(stranger)


def post_project(client, headers, name="Study"):
    response = client.post("/api/projects", headers=headers, json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def post_experiment(client, headers, project_id, **changes):
    response = client.post(f"/api/projects/{project_id}/experiments", headers=headers,
                           json={**EXPERIMENT, **changes})
    assert response.status_code == 201, response.text
    return response.json()


def test_project_crud_soft_delete_and_public_schema(client, auth_headers, db_session):
    created = post_project(client, auth_headers, "  Research  ")
    project_id = UUID(created["id"])
    assert created["name"] == "Research"
    assert "user_id" not in created
    assert created["created_at"].endswith("Z")
    assert client.get(f"/api/projects/{project_id}", headers=auth_headers).json() == created
    assert client.get("/api/projects", headers=auth_headers).json()["items"] == [created]
    edited = client.patch(f"/api/projects/{project_id}", headers=auth_headers,
                          json={"name": "Revised", "description": "Question"})
    assert edited.status_code == 200
    assert edited.json()["description"] == "Question"
    cleared = client.patch(f"/api/projects/{project_id}", headers=auth_headers,
                           json={"description": None})
    assert cleared.json()["description"] is None
    deleted = client.delete(f"/api/projects/{project_id}", headers=auth_headers)
    assert deleted.status_code == 204 and deleted.content == b""
    assert db_session.get(models.ResearchProject, project_id).deleted_at is not None
    assert client.get(f"/api/projects/{project_id}", headers=auth_headers).status_code == 404
    assert client.get("/api/projects", headers=auth_headers).json()["items"] == []


def test_experiment_crud_clone_archive_and_duplicate_names(client, auth_headers, db_session):
    first = post_project(client, auth_headers)
    second = post_project(client, auth_headers)
    original = post_experiment(client, auth_headers, first["id"], hypothesis="Hypothesis")
    duplicate = post_experiment(client, auth_headers, second["id"])
    assert original["name"] == duplicate["name"] == "Baseline"
    experiment_id = original["id"]
    assert client.get(f"/api/experiments/{experiment_id}", headers=auth_headers).json() == original
    listed = client.get(f"/api/projects/{first['id']}/experiments", headers=auth_headers).json()
    assert listed["items"] == [original]
    updated = client.patch(f"/api/experiments/{experiment_id}", headers=auth_headers,
                           json={"notes": "Evidence", "config": {"numOfTXperBlock": 9}})
    assert updated.status_code == 200
    assert updated.json()["config"]["numOfTXperBlock"] == 9
    clone = client.post(f"/api/experiments/{experiment_id}/clone", headers=auth_headers,
                        json={"name": "Variant", "project_id": second["id"]})
    assert clone.status_code == 201
    assert clone.json()["id"] != experiment_id
    assert clone.json()["project_id"] == second["id"]
    assert clone.json()["config"] == updated.json()["config"]
    assert clone.json()["default_seed"] == 42
    assert clone.json()["hypothesis"] == "Hypothesis"
    assert clone.json()["notes"] == "Evidence"
    default_clone = client.post(f"/api/experiments/{experiment_id}/clone", headers=auth_headers, json={})
    assert default_clone.status_code == 201
    assert default_clone.json()["name"] == "Baseline copy"
    archived = client.delete(f"/api/experiments/{experiment_id}", headers=auth_headers)
    assert archived.status_code == 204 and archived.content == b""
    assert db_session.get(models.Experiment, UUID(experiment_id)).archived_at is not None
    assert client.get(f"/api/experiments/{experiment_id}", headers=auth_headers).status_code == 404
    assert experiment_id not in [row["id"] for row in client.get(
        f"/api/projects/{first['id']}/experiments", headers=auth_headers).json()["items"]]


@pytest.mark.parametrize("status", ["queued", "running"])
def test_project_delete_conflicts_with_active_run(client, workspace, db_session, status):
    _, _, project, _, run, headers, _ = workspace
    run.status = status
    db_session.commit()
    assert client.delete(f"/api/projects/{project.id}", headers=headers).status_code == 409
    assert client.get(f"/api/projects/{project.id}", headers=headers).status_code == 200
    run.status = "completed"
    db_session.commit()
    assert client.delete(f"/api/projects/{project.id}", headers=headers).status_code == 204


def test_cursor_pages_and_run_filters(client, workspace, db_session):
    owner, stranger, project, experiment, run, headers, _ = workspace
    other = post_project(client, headers, "Other")
    newest = post_project(client, headers, "Newest")
    first = client.get("/api/projects?limit=2", headers=headers).json()
    assert [row["id"] for row in first["items"]] == [newest["id"], other["id"]]
    second = client.get("/api/projects", headers=headers,
                        params={"limit": 2, "cursor": first["next_cursor"]}).json()
    assert [row["id"] for row in second["items"]] == [str(project.id)]
    assert second["next_cursor"] is None
    experiments = [post_experiment(client, headers, project.id) for _ in range(2)]
    page = client.get(f"/api/projects/{project.id}/experiments?limit=2", headers=headers).json()
    assert [row["id"] for row in page["items"]] == [row["id"] for row in reversed(experiments)]
    tail = client.get(f"/api/projects/{project.id}/experiments", headers=headers,
                      params={"cursor": page["next_cursor"], "limit": 2}).json()
    assert [row["id"] for row in tail["items"]] == [str(experiment.id)]
    assert tail["next_cursor"] is None
    completed = models.Simulation(user_id=owner.id, experiment_id=experiment.id, status="completed")
    failed = models.Simulation(user_id=owner.id, status="failed")
    foreign = models.Simulation(user_id=stranger.id, status="completed")
    db_session.add_all([completed, failed, foreign])
    db_session.commit()
    page = client.get("/api/runs?limit=2", headers=headers).json()
    assert [row["id"] for row in page["items"]] == [str(failed.public_id), str(completed.public_id)]
    tail = client.get("/api/runs", headers=headers,
                      params={"limit": 2, "cursor": page["next_cursor"]}).json()
    assert [row["id"] for row in tail["items"]] == [str(run.public_id)]
    assert tail["next_cursor"] is None
    for filters in ({"project_id": str(project.id)}, {"experiment_id": str(experiment.id)},
                    {"status": "completed"},
                    {"project_id": str(project.id), "experiment_id": str(experiment.id), "status": "completed"}):
        response = client.get("/api/runs", headers=headers, params=filters)
        assert response.status_code == 200
        assert [row["id"] for row in response.json()["items"]] == [str(completed.public_id), str(run.public_id)]
    assert client.get("/api/runs", headers=headers,
                      params={"project_id": other["id"], "experiment_id": str(experiment.id)}).json()["items"] == []
    assert "public_id" not in tail["items"][0] and "user_id" not in tail["items"][0]


def test_history_survives_archive_delete_and_nullable_legacy_rows(client, workspace, db_session):
    _, _, project, experiment, run, headers, stranger_headers = workspace
    db_session.execute(update(models.Simulation).where(models.Simulation.id == run.id).values(
        status=None, started_at=None, ended_at=None, avg_cpu=None, energy_used=None, blocks_mined=None))
    db_session.commit()
    assert client.delete(f"/api/experiments/{experiment.id}", headers=headers).status_code == 204
    assert client.delete(f"/api/projects/{project.id}", headers=headers).status_code == 204
    for filters in ({}, {"project_id": str(project.id)}, {"experiment_id": str(experiment.id)}):
        response = client.get("/api/runs", headers=headers, params=filters)
        assert response.status_code == 200
        assert response.json()["items"][0]["status"] is None
    for filters in ({"project_id": str(project.id)}, {"experiment_id": str(experiment.id)}):
        response = client.get("/api/runs", headers=stranger_headers, params=filters)
        assert response.status_code == 404
        assert response.json() == {"detail": "Not found"}
    assert client.get(f"/api/projects/{project.id}/experiments", headers=headers).status_code == 404
    assert client.get(f"/api/experiments/{experiment.id}", headers=headers).status_code == 404
    history = client.get("/api/simulations", headers=headers)
    assert history.status_code == 200
    assert history.json() == [{
        "id": str(run.public_id), "function": None, "placement": None, "consensus": None,
        "status": None, "started_at": None, "ended_at": None, "blocks_mined": None,
        "avg_cpu": None, "energy_used": None,
    }]


def test_compatibility_history_keeps_shape_rounds_and_reads_all_owner_pages(client, workspace, db_session):
    owner, stranger, _, _, run, headers, _ = workspace
    run.avg_cpu, run.energy_used = 1.2345, 0.12345678
    db_session.add_all([models.Simulation(user_id=owner.id, status="completed") for _ in range(101)])
    db_session.add(models.Simulation(user_id=stranger.id, status="completed"))
    db_session.commit()
    history = client.get("/api/simulations", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 102
    assert {row["id"] for row in history.json()} == {
        str(row.public_id) for row in db_session.query(models.Simulation).filter_by(user_id=owner.id)}
    old = next(row for row in history.json() if row["id"] == str(run.public_id))
    assert set(old) == {"id", "function", "placement", "consensus", "status", "started_at",
                        "ended_at", "blocks_mined", "avg_cpu", "energy_used"}
    assert old["avg_cpu"] == 1.23 and old["energy_used"] == 0.123457


def test_compatibility_history_sorts_start_times_then_uuid_with_nulls_last(client, workspace, db_session):
    owner, _, _, _, original, headers, _ = workspace
    original.public_id = UUID("00000000-0000-0000-0000-000000000002")
    original.started_at = datetime(2023, 1, 1, tzinfo=timezone.utc)
    # Insertions deliberately disagree with start times and the UUID tie-breaker.
    latest = models.Simulation(user_id=owner.id, status="completed",
        public_id=UUID("00000000-0000-0000-0000-000000000001"),
        started_at=datetime(2025, 1, 1, tzinfo=timezone.utc))
    tie_high = models.Simulation(user_id=owner.id, status="completed",
        public_id=UUID("00000000-0000-0000-0000-000000000009"),
        started_at=datetime(2024, 1, 1, tzinfo=timezone.utc))
    tie_low = models.Simulation(user_id=owner.id, status="completed",
        public_id=UUID("00000000-0000-0000-0000-000000000003"),
        started_at=datetime(2024, 1, 1, tzinfo=timezone.utc))
    missing = models.Simulation(user_id=owner.id, status="completed",
        public_id=UUID("00000000-0000-0000-0000-000000000007"))
    db_session.add_all([latest, tie_high, tie_low, missing])
    db_session.commit()
    db_session.execute(update(models.Simulation).where(models.Simulation.id == missing.id).values(started_at=None))
    db_session.commit()
    history = client.get("/api/simulations", headers=headers)
    assert history.status_code == 200
    assert [row["id"] for row in history.json()] == [
        "00000000-0000-0000-0000-000000000001",
        "00000000-0000-0000-0000-000000000009",
        "00000000-0000-0000-0000-000000000003",
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000007",
    ]
    # Modern run pagination retains insertion order.
    assert [row["id"] for row in client.get("/api/runs", headers=headers).json()["items"]] == [
        "00000000-0000-0000-0000-000000000007",
        "00000000-0000-0000-0000-000000000003",
        "00000000-0000-0000-0000-000000000009",
        "00000000-0000-0000-0000-000000000001",
        "00000000-0000-0000-0000-000000000002",
    ]


def test_compatibility_history_has_explicit_nullable_public_openapi_contract(client, workspace, db_session):
    _, _, _, _, run, headers, _ = workspace
    run.function, run.placement, run.consensus = "Data Management", "Fog", "PoW"
    run.started_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    run.ended_at = datetime(2025, 1, 2, tzinfo=timezone.utc)
    run.blocks_mined, run.avg_cpu, run.energy_used = 3, 1.2345, 0.12345678
    db_session.commit()
    response = client.get("/api/simulations", headers=headers)
    assert response.status_code == 200
    document = client.get("/openapi.json").json()
    schema = document["paths"]["/api/simulations"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["type"] == "array"
    assert "$ref" in schema["items"]
    item = document["components"]["schemas"][schema["items"]["$ref"].rsplit("/", 1)[1]]
    expected_types = {
        "function": "string", "placement": "string", "consensus": "string", "status": "string",
        "started_at": "string", "ended_at": "string", "blocks_mined": "integer",
        "avg_cpu": "number", "energy_used": "number",
    }
    assert set(item["properties"]) == {"id", *expected_types}
    assert set(item["required"]) == {"id", *expected_types}
    assert item["properties"]["id"]["type"] == "string"
    assert item["properties"]["id"]["format"] == "uuid"
    for field, kind in expected_types.items():
        branches = item["properties"][field]["anyOf"]
        assert {branch["type"] for branch in branches} == {kind, "null"}
        if field in {"started_at", "ended_at"}:
            assert next(branch for branch in branches if branch["type"] == "string")["format"] == "date-time"
    assert response.json() == [{
        "id": str(run.public_id), "function": "Data Management", "placement": "Fog", "consensus": "PoW",
        "status": "completed", "started_at": "2025-01-01T00:00:00Z", "ended_at": "2025-01-02T00:00:00Z",
        "blocks_mined": 3, "avg_cpu": 1.23, "energy_used": 0.123457,
    }]


def test_all_foreign_and_unknown_resource_requests_are_indistinguishable(client, workspace):
    _, _, project, experiment, _, _, headers = workspace
    for project_id in (project.id, uuid4()):
        for method, path, data in [
            ("GET", f"/api/projects/{project_id}", None),
            ("PATCH", f"/api/projects/{project_id}", {"name": "Stolen"}),
            ("DELETE", f"/api/projects/{project_id}", None),
            ("GET", f"/api/projects/{project_id}/experiments", None),
            ("POST", f"/api/projects/{project_id}/experiments", EXPERIMENT),
            ("GET", f"/api/runs?project_id={project_id}", None),
        ]:
            response = client.request(method, path, headers=headers, **({"json": data} if data is not None else {}))
            assert response.status_code == 404, (method, path, response.text)
            assert response.json() == {"detail": "Not found"}
    for experiment_id in (experiment.id, uuid4()):
        for method, path, data in [
            ("GET", f"/api/experiments/{experiment_id}", None),
            ("PATCH", f"/api/experiments/{experiment_id}", {"name": "Stolen"}),
            ("DELETE", f"/api/experiments/{experiment_id}", None),
            ("POST", f"/api/experiments/{experiment_id}/clone", {}),
            ("GET", f"/api/runs?experiment_id={experiment_id}", None),
        ]:
            response = client.request(method, path, headers=headers, **({"json": data} if data is not None else {}))
            assert response.status_code == 404
            assert response.json() == {"detail": "Not found"}


def test_clone_target_project_and_combined_filters_are_owner_checked(client, workspace):
    _, _, project, experiment, _, owner_headers, stranger_headers = workspace
    own = post_project(client, stranger_headers)
    stranger_experiment = post_experiment(client, stranger_headers, own["id"])
    assert [row["id"] for row in client.get("/api/projects", headers=stranger_headers).json()["items"]] == [own["id"]]
    listed = client.get(f"/api/projects/{own['id']}/experiments", headers=stranger_headers).json()
    assert [row["id"] for row in listed["items"]] == [stranger_experiment["id"]]
    for target in (project.id, uuid4()):
        response = client.post(f"/api/experiments/{stranger_experiment['id']}/clone",
                               headers=stranger_headers, json={"project_id": str(target)})
        assert response.status_code == 404
        assert response.json() == {"detail": "Not found"}
    for filters in ({"project_id": own["id"], "experiment_id": str(experiment.id)},
                    {"project_id": str(project.id), "experiment_id": stranger_experiment["id"]}):
        response = client.get("/api/runs", headers=owner_headers, params=filters)
        assert response.status_code == 404


def test_foreign_cursor_tokens_are_empty_nonleaking_continuations(client, workspace):
    _, _, project, experiment, run, _, headers = workspace
    own = post_project(client, headers)
    for path, foreign_cursor in (("/api/projects", project.id),
                                  (f"/api/projects/{own['id']}/experiments", experiment.id),
                                  ("/api/runs", run.public_id)):
        for cursor in (foreign_cursor, uuid4()):
            response = client.get(path, headers=headers, params={"cursor": str(cursor)})
            assert response.status_code == 200
            assert response.json() == {"items": [], "next_cursor": None}


@pytest.mark.parametrize("path", ["/api/projects", "/api/projects/{}", "/api/projects/{}/experiments",
                                  "/api/experiments/{}", "/api/runs", "/api/simulations"])
def test_research_reads_require_authentication(client, path):
    assert client.get(path.format(uuid4())).status_code == 401


def test_research_writes_require_authentication(client):
    for method, path, data in [
        ("POST", "/api/projects", {"name": "Study"}),
        ("PATCH", f"/api/projects/{uuid4()}", {"name": "Edit"}),
        ("DELETE", f"/api/projects/{uuid4()}", None),
        ("POST", f"/api/projects/{uuid4()}/experiments", EXPERIMENT),
        ("PATCH", f"/api/experiments/{uuid4()}", {"name": "Edit"}),
        ("DELETE", f"/api/experiments/{uuid4()}", None),
        ("POST", f"/api/experiments/{uuid4()}/clone", {}),
    ]:
        assert client.request(method, path, **({"json": data} if data is not None else {})).status_code == 401


def test_request_field_and_pagination_bounds(client, workspace):
    _, _, project, experiment, _, headers, _ = workspace
    for name in ("", "   ", "x" * 121):
        assert client.post("/api/projects", headers=headers, json={"name": name}).status_code == 422
        assert client.patch(f"/api/projects/{project.id}", headers=headers, json={"name": name}).status_code == 422
    assert post_project(client, headers, "x" * 120)["name"] == "x" * 120
    for name in ("", "   ", "x" * 161):
        assert client.post(f"/api/projects/{project.id}/experiments", headers=headers,
                           json={**EXPERIMENT, "name": name}).status_code == 422
        assert client.patch(f"/api/experiments/{experiment.id}", headers=headers,
                            json={"name": name}).status_code == 422
        assert client.post(f"/api/experiments/{experiment.id}/clone", headers=headers,
                           json={"name": name}).status_code == 422
    assert post_experiment(client, headers, project.id, name="x" * 160)["name"] == "x" * 160
    for path in ("/api/projects", f"/api/projects/{project.id}/experiments", "/api/runs"):
        for limit in (0, -1, 101, "abc"):
            assert client.get(path, headers=headers, params={"limit": limit}).status_code == 422
        for limit in (1, 100):
            assert client.get(path, headers=headers, params={"limit": limit}).status_code == 200
        assert client.get(path, headers=headers, params={"cursor": "1"}).status_code == 422
    for filters in ({"project_id": "1"}, {"experiment_id": "1"}, {"status": "unknown"}):
        assert client.get("/api/runs", headers=headers, params=filters).status_code == 422
    for path in ("/api/projects/1", "/api/projects/1/experiments", "/api/experiments/1"):
        assert client.get(path, headers=headers).status_code == 422


def test_service_validation_errors_are_client_errors(client, workspace):
    _, _, _, experiment, _, headers, _ = workspace
    # Placement validation happens inside the service after merging the stored template.
    response = client.patch(f"/api/experiments/{experiment.id}", headers=headers,
                            json={"blockchain_placement": 2, "config": {"NumOfMiners": 1}})
    assert response.status_code == 422


def test_routers_registered_once_per_app(client):
    from api.app_factory import create_app
    for app in (client.app, create_app()):
        routes = [(route.path, method) for route in app.routes for method in getattr(route, "methods", ())]
        assert len(routes) == len(set(routes))
