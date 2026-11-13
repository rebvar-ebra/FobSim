"""Final-review regressions: engine inputs, hosted budgets, and mutable cursors."""

import json
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

import auth
import models
import server
from api.config_schema import SimulationConfig, to_engine_config
from api.schemas.experiments import ExperimentCreate, ExperimentUpdate, ExperimentClone
from api.schemas.projects import ProjectCreate
from api.services import experiments, projects, runs


BASE = {"blockchain_function": 1, "blockchain_placement": 1, "consensus_algorithm": 1}
ONE_MINER = {"NumOfFogNodes": 1, "NumOfMiners": 1,
             "number_of_each_miner_neighbours": 0, "Num_of_DPoS_delegates": 1}

# Literal counts independently derived from main.py's workload construction.
INVALID_INPUTS = [
    pytest.param({"blockchain_function": 3}, {"Max_enduser_payment": 0}, id="zero-payment"),
    pytest.param({"consensus_algorithm": 5, "blockchain_placement": 1}, ONE_MINER, id="one-fog-dpos"),
    pytest.param({"consensus_algorithm": 5, "blockchain_placement": 2}, ONE_MINER, id="one-enduser-dpos"),
    pytest.param({}, {"puzzle_difficulty": 4}, id="pow-difficulty"),
    pytest.param({}, {"NumOfFogNodes": 6, "num_of_users_per_fog_node": 84,
                      "NumOfTaskPerUser": 1}, id="504-users"),
    pytest.param({}, {"NumOfFogNodes": 5, "num_of_users_per_fog_node": 100,
                      "NumOfTaskPerUser": 11, "numOfTXperBlock": 10}, id="5500-tasks"),
    pytest.param({}, {"NumOfFogNodes": 7, "num_of_users_per_fog_node": 11,
                      "NumOfTaskPerUser": 13, "numOfTXperBlock": 1}, id="1001-blocks"),
    pytest.param({}, {"NumOfFogNodes": 3, "num_of_users_per_fog_node": 23,
                      "NumOfTaskPerUser": 29, "numOfTXperBlock": 2}, id="ceil-1001-blocks"),
    pytest.param({"blockchain_function": 2}, {"NumOfFogNodes": 7, "num_of_users_per_fog_node": 11,
                      "NumOfTaskPerUser": 13, "numOfTXperBlock": 10000}, id="1001-compute-blocks"),
    pytest.param({}, {"NumOfFogNodes": 5, "num_of_users_per_fog_node": 13,
                      "NumOfTaskPerUser": 1, "numOfTXperBlock": 1,
                      "Parallel_PoW_mining": True}, id="65-pow-processes"),
    pytest.param({}, {"NumOfFogNodes": 3, "num_of_users_per_fog_node": 43,
                      "NumOfTaskPerUser": 1, "numOfTXperBlock": 2,
                      "Parallel_PoW_mining": True}, id="ceil-65-pow-processes"),
    pytest.param({"blockchain_function": 2}, {"NumOfFogNodes": 5, "num_of_users_per_fog_node": 13,
                      "NumOfTaskPerUser": 1, "numOfTXperBlock": 10000,
                      "Parallel_PoW_mining": True}, id="65-compute-pow-processes"),
]


@pytest.mark.parametrize("selectors,config", INVALID_INPUTS)
def test_effective_config_rejects_engine_invalid_and_over_budget_work(selectors, config):
    with pytest.raises(ValidationError):
        server.RunSimulation(**{**BASE, **selectors}, config=config).effective_config({})


@pytest.mark.parametrize("selectors,config", [
    ({"blockchain_function": 3}, {"Max_enduser_payment": 1}),
    *[({"blockchain_function": function}, {"Max_enduser_payment": 0}) for function in (1, 2, 4, 5)],
    *[({"consensus_algorithm": 5, "blockchain_placement": placement},
       {**ONE_MINER, "NumOfFogNodes": 2, "NumOfMiners": 2}) for placement in (1, 2)],
    ({"consensus_algorithm": 1}, ONE_MINER),
    ({}, {"puzzle_difficulty": 3}),
    ({}, {"NumOfFogNodes": 5, "num_of_users_per_fog_node": 100, "NumOfTaskPerUser": 1}),  # 500 users
    ({}, {"NumOfFogNodes": 5, "num_of_users_per_fog_node": 100, "NumOfTaskPerUser": 10}),  # 5000 tasks, 1000 blocks
    ({"blockchain_function": 2}, {"NumOfFogNodes": 5, "num_of_users_per_fog_node": 100,
                                 "NumOfTaskPerUser": 2, "numOfTXperBlock": 10000}),  # 1000 compute blocks
    ({}, {"NumOfFogNodes": 7, "num_of_users_per_fog_node": 11,
          "NumOfTaskPerUser": 13, "numOfTXperBlock": 2}),  # ceil(1001/2) = 501
    ({}, {"NumOfFogNodes": 4, "num_of_users_per_fog_node": 16, "NumOfTaskPerUser": 1,
          "numOfTXperBlock": 1, "Parallel_PoW_mining": True}),  # 64 processes
    ({}, {"NumOfFogNodes": 4, "num_of_users_per_fog_node": 16, "NumOfTaskPerUser": 2,
          "numOfTXperBlock": 2, "Parallel_PoW_mining": True}),  # 64 processes with batching
    ({"consensus_algorithm": 2}, {"NumOfFogNodes": 5, "num_of_users_per_fog_node": 13,
          "NumOfTaskPerUser": 1, "numOfTXperBlock": 1, "Parallel_PoW_mining": True}),
    ({}, {"NumOfFogNodes": 5, "num_of_users_per_fog_node": 13,
          "NumOfTaskPerUser": 1, "numOfTXperBlock": 1, "Parallel_PoW_mining": False}),
])
def test_effective_config_accepts_safe_adjacent_workloads(selectors, config):
    effective = server.RunSimulation(**{**BASE, **selectors}, config=config).effective_config({})
    assert all(getattr(effective, field) == value for field, value in config.items())


@pytest.mark.parametrize("field", list(BASE))
@pytest.mark.parametrize("value", [True, False, 1.0, "1", 7])
def test_shared_boundary_requires_strict_known_selectors(field, value):
    from api.config_schema import validate_effective_config

    with pytest.raises(ValidationError):
        validate_effective_config({}, **{**BASE, field: value})


def test_shared_boundary_revalidates_mutated_models_and_placement_first():
    from api.config_schema import validate_effective_config

    config = SimulationConfig()
    config.NumOfFogNodes = 1
    config.Max_enduser_payment = 0
    with pytest.raises(ValidationError, match="effective miner count"):
        validate_effective_config(config, **{**BASE, "blockchain_function": 3})


@pytest.fixture
def workspace(db_session, user_factory):
    owner = user_factory()
    project = projects.create_project(db_session, owner.id, ProjectCreate(name="Study"))
    headers = {"Authorization": f"Bearer {auth.create_access_token({'sub': owner.email})}"}
    return owner, project, headers


@pytest.fixture
def isolated_engine_file(tmp_path, monkeypatch):
    (tmp_path / "api").mkdir()
    monkeypatch.setattr(server, "__file__", str(tmp_path / "api" / "server.py"))
    path = tmp_path / "Sim_parameters.json"
    path.write_text(json.dumps(to_engine_config(SimulationConfig())))
    # Keep a RED regression from launching an actual expensive/invalid engine.
    monkeypatch.setattr(server, "execute_simulation", AsyncMock())
    monkeypatch.setattr(server, "simulation_running", False)
    return path


@pytest.mark.parametrize("selectors,config", INVALID_INPUTS)
def test_rejected_http_run_writes_neither_file_nor_row(
    client, db_session, workspace, isolated_engine_file, selectors, config,
):
    _, _, headers = workspace
    original = isolated_engine_file.read_text()
    response = client.post("/api/run", headers=headers, json={**BASE, **selectors, "config": config})
    assert response.status_code == 422, response.text
    assert isolated_engine_file.read_text() == original
    assert db_session.query(models.Simulation).count() == 0


@pytest.mark.parametrize("selectors,config", INVALID_INPUTS)
@pytest.mark.parametrize("boundary", ["service", "http"])
def test_rejected_experiment_create_and_update_do_not_write(
    client, db_session, workspace, selectors, config, boundary,
):
    owner, project, headers = workspace
    original = experiments.create_experiment(db_session, owner.id, project.id,
        ExperimentCreate(name="Original", **BASE))
    before = (original.config.copy(), original.updated_at, original.blockchain_function,
              original.blockchain_placement, original.consensus_algorithm)
    invalid = {**BASE, **selectors, "name": "Invalid", "config": config}
    if boundary == "service":
        with pytest.raises(ValidationError):
            experiments.create_experiment(db_session, owner.id, project.id, ExperimentCreate(**invalid))
        with pytest.raises(ValidationError):
            experiments.update_experiment(db_session, owner.id, original.id, ExperimentUpdate(**invalid))
    else:
        assert client.post(f"/api/projects/{project.id}/experiments", headers=headers,
                           json=invalid).status_code == 422
        assert client.patch(f"/api/experiments/{original.id}", headers=headers,
                            json=invalid).status_code == 422
    assert not db_session.dirty
    db_session.expire_all()
    assert db_session.query(models.Experiment).count() == 1
    assert original.name == "Original"
    assert (original.config, original.updated_at, original.blockchain_function,
            original.blockchain_placement, original.consensus_algorithm) == before


@pytest.mark.parametrize("initial,change", [
    ({"config": {"Max_enduser_payment": 0}}, {"blockchain_function": 3}),
    ({"config": ONE_MINER}, {"consensus_algorithm": 5}),
    ({"blockchain_placement": 2, "consensus_algorithm": 5,
      "config": {**ONE_MINER, "NumOfMiners": 2}}, {"blockchain_placement": 1}),
    ({"config": {"NumOfFogNodes": 7, "num_of_users_per_fog_node": 11,
                 "NumOfTaskPerUser": 13, "numOfTXperBlock": 2}}, {"blockchain_function": 2}),
    ({"consensus_algorithm": 2, "config": {"NumOfFogNodes": 5, "num_of_users_per_fog_node": 13,
      "NumOfTaskPerUser": 1, "numOfTXperBlock": 1, "Parallel_PoW_mining": True}}, {"consensus_algorithm": 1}),
])
@pytest.mark.parametrize("boundary", ["service", "http"])
def test_selector_only_edits_and_clones_revalidate_merged_config(
    client, db_session, workspace, initial, change, boundary,
):
    owner, project, headers = workspace
    row = experiments.create_experiment(db_session, owner.id, project.id,
        ExperimentCreate(**{"name": "Original", **BASE, **initial}))
    before = {key: getattr(row, key) for key in (*BASE, "config", "updated_at")}
    if boundary == "service":
        with pytest.raises(ValidationError):
            experiments.update_experiment(db_session, owner.id, row.id, ExperimentUpdate(**change))
    else:
        assert client.patch(f"/api/experiments/{row.id}", headers=headers, json=change).status_code == 422
    assert not db_session.dirty
    db_session.expire_all()
    assert {key: getattr(row, key) for key in before} == before
    # Simulate an older stored template that predates the strengthened boundary.
    for key, value in change.items():
        setattr(row, key, str(value))
    db_session.commit()
    if boundary == "service":
        with pytest.raises(ValidationError):
            experiments.clone_experiment(db_session, owner.id, row.id, ExperimentClone())
    else:
        assert client.post(f"/api/experiments/{row.id}/clone", headers=headers, json={}).status_code == 422
    assert db_session.query(models.Experiment).count() == 1


@pytest.mark.parametrize("resource", ["projects", "experiments", "runs"])
@pytest.mark.parametrize("boundary", ["service", "http"])
def test_cursor_continues_after_anchor_visibility_changes(
    client, db_session, workspace, user_factory, resource, boundary,
):
    owner, project, headers = workspace
    if resource == "projects":
        # Include the fixture project in the three rows under test.
        for _ in range(2):
            projects.create_project(db_session, owner.id, ProjectCreate(name="Next"))
        url, params = "/api/projects", {}
        service = lambda **kw: projects.list_owned_projects(db_session, owner.id, **kw)
        mutate = lambda anchor: projects.delete_project(db_session, owner.id, anchor)
    else:
        experiment = experiments.create_experiment(db_session, owner.id, project.id,
            ExperimentCreate(name="First", **BASE))
        if resource == "experiments":
            for _ in range(2):
                experiments.create_experiment(db_session, owner.id, project.id,
                    ExperimentCreate(name="Next", **BASE))
            url, params = f"/api/projects/{project.id}/experiments", {}
            service = lambda **kw: experiments.list_owned_experiments(db_session, owner.id, project.id, **kw)
            mutate = lambda anchor: experiments.archive_experiment(db_session, owner.id, anchor)
        else:
            for _ in range(3):
                db_session.add(models.Simulation(user_id=owner.id, experiment_id=experiment.id, status="queued"))
            db_session.commit()
            # The continuation must retain both parent scope and the requested status.
            db_session.add(models.Simulation(user_id=owner.id, experiment_id=experiment.id, status="failed"))
            db_session.commit()
            url = "/api/runs"
            params = {"project_id": project.id, "experiment_id": experiment.id, "status": "queued"}
            service = lambda **kw: runs.list_owned_runs(db_session, owner.id, **params, **kw)

            def mutate(anchor):
                runs.get_owned_run(db_session, owner.id, anchor).status = "completed"
                db_session.commit()

    def page(**kw):
        if boundary == "service":
            return service(**kw).model_dump(mode="json")
        response = client.get(url, headers=headers, params={**params, **kw})
        assert response.status_code == 200
        return response.json()

    expected = [item["id"] for item in page()["items"]]
    first = page(limit=1)
    mutate(UUID(first["next_cursor"]))
    second = page(limit=1, cursor=UUID(first["next_cursor"]))
    assert [item["id"] for item in second["items"]] == [expected[1]]
    assert second["next_cursor"] == expected[1]
    last = page(limit=1, cursor=UUID(second["next_cursor"]))
    assert [item["id"] for item in last["items"]] == [expected[2]]
    assert last["next_cursor"] is None
    assert page(cursor=uuid4()) == {"items": [], "next_cursor": None}

    # Hidden anchors must still be owned and belong to the immutable parent scope.
    stranger = user_factory()
    foreign_project = projects.create_project(db_session, stranger.id, ProjectCreate(name="Private"))
    foreign_experiment = experiments.create_experiment(db_session, stranger.id, foreign_project.id,
        ExperimentCreate(name="Private", **BASE))
    wrong_scope_experiment = experiments.create_experiment(db_session, owner.id,
        projects.create_project(db_session, owner.id, ProjectCreate(name="Other")).id,
        ExperimentCreate(name="Other", **BASE))
    if resource == "projects":
        projects.delete_project(db_session, stranger.id, foreign_project.id)
        anchors = [foreign_project.id]
    elif resource == "experiments":
        experiments.archive_experiment(db_session, stranger.id, foreign_experiment.id)
        experiments.archive_experiment(db_session, owner.id, wrong_scope_experiment.id)
        anchors = [foreign_experiment.id, wrong_scope_experiment.id]
    else:
        anchors = []
        for user, scope in ((stranger, foreign_experiment), (owner, wrong_scope_experiment)):
            row = models.Simulation(user_id=user.id, experiment_id=scope.id, status="completed")
            db_session.add(row)
            db_session.commit()
            anchors.append(row.public_id)
    for anchor in anchors:
        assert page(cursor=anchor) == {"items": [], "next_cursor": None}
