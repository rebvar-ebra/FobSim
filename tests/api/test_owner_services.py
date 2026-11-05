"""Ownership, persistence, and public contracts for research services."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

import models
from api.services.projects import (
    ActiveRunsError, create_project, get_owned_project, list_owned_projects,
    update_project, delete_project,
)
from api.services.experiments import (
    create_experiment, get_owned_experiment, list_owned_experiments,
    update_experiment, archive_experiment, clone_experiment,
)
from api.services.runs import get_owned_run, list_owned_runs
from api.schemas.projects import ProjectCreate, ProjectUpdate, ProjectResponse
from api.schemas.experiments import (
    ExperimentCreate, ExperimentUpdate, ExperimentClone, ExperimentResponse,
)
from api.schemas.runs import RunResponse


@pytest.fixture
def owners(user_factory):
    return user_factory(), user_factory()


def experiment_data(**overrides):
    return ExperimentCreate(**{
        "name": "Baseline", "blockchain_function": 1,
        "blockchain_placement": 1, "consensus_algorithm": 1, "config": {},
        **overrides,
    })


def make_experiment(db, owner, **overrides):
    project = create_project(db, owner.id, ProjectCreate(name="Study"))
    return create_experiment(db, owner.id, project.id, experiment_data(**overrides))


def make_run(db, owner, experiment=None, **overrides):
    row = models.Simulation(**{
        "user_id": owner.id, "experiment_id": experiment.id if experiment else None,
        "status": "completed", "config": dict(experiment.config) if experiment else {"legacy": 3},
        "function": "Data Management", "placement": "Fog", "consensus": "PoW",
        **overrides,
    })
    db.add(row)
    db.commit()
    return row


def test_owner_lookups_and_mutations_hide_foreign_and_unknown_uuids(db_session, owners):
    owner, stranger = owners
    experiment = make_experiment(db_session, owner)
    project_id, experiment_id = experiment.project_id, experiment.id
    run = make_run(db_session, owner, experiment)
    assert get_owned_project(db_session, owner.id, project_id).id == project_id
    assert get_owned_experiment(db_session, owner.id, experiment_id).id == experiment_id
    assert get_owned_run(db_session, owner.id, run.public_id).id == run.id
    for foreign_id in (project_id, uuid4()):
        assert get_owned_project(db_session, stranger.id, foreign_id) is None
        assert update_project(db_session, stranger.id, foreign_id, ProjectUpdate(name="Stolen")) is None
        assert delete_project(db_session, stranger.id, foreign_id) is None
        assert create_experiment(db_session, stranger.id, foreign_id, experiment_data()) is None
        assert list_owned_experiments(db_session, stranger.id, foreign_id).items == []
    for foreign_id in (experiment_id, uuid4()):
        assert get_owned_experiment(db_session, stranger.id, foreign_id) is None
        assert update_experiment(db_session, stranger.id, foreign_id, ExperimentUpdate(name="Stolen")) is None
        assert archive_experiment(db_session, stranger.id, foreign_id) is None
        assert clone_experiment(db_session, stranger.id, foreign_id, ExperimentClone()) is None
    for foreign_id in (run.public_id, uuid4()):
        assert get_owned_run(db_session, stranger.id, foreign_id) is None
    assert get_owned_project(db_session, owner.id, project_id).name == "Study"


def test_project_update_and_soft_delete_preserve_historical_runs(db_session, owners):
    owner, _ = owners
    experiment = make_experiment(db_session, owner)
    run = make_run(db_session, owner, experiment)
    project = update_project(db_session, owner.id, experiment.project_id, ProjectUpdate(description="Evidence"))
    assert project.description == "Evidence" and project.name == "Study"
    assert delete_project(db_session, owner.id, project.id).deleted_at is not None
    assert get_owned_project(db_session, owner.id, project.id) is None
    assert get_owned_experiment(db_session, owner.id, experiment.id) is None
    assert list_owned_projects(db_session, owner.id).items == []
    assert list_owned_experiments(db_session, owner.id, project.id).items == []
    assert get_owned_run(db_session, owner.id, run.public_id).config == run.config
    assert [item.id for item in list_owned_runs(db_session, owner.id, project_id=project.id).items] == [run.public_id]


@pytest.mark.parametrize("status", ["queued", "running"])
def test_project_delete_rejects_active_runs_even_in_archived_experiments(db_session, owners, status):
    owner, _ = owners
    experiment = make_experiment(db_session, owner)
    make_run(db_session, owner, experiment, status=status)
    archive_experiment(db_session, owner.id, experiment.id)
    with pytest.raises(ActiveRunsError):
        delete_project(db_session, owner.id, experiment.project_id)
    assert get_owned_project(db_session, owner.id, experiment.project_id) is not None


def test_archive_hides_template_but_preserves_run_history(db_session, owners):
    owner, stranger = owners
    experiment = make_experiment(db_session, owner)
    run = make_run(db_session, owner, experiment)
    assert archive_experiment(db_session, owner.id, experiment.id).archived_at is not None
    assert get_owned_experiment(db_session, owner.id, experiment.id) is None
    assert list_owned_experiments(db_session, owner.id, experiment.project_id).items == []
    assert get_owned_run(db_session, owner.id, run.public_id) is not None
    assert len(list_owned_runs(db_session, owner.id, experiment_id=experiment.id).items) == 1
    assert list_owned_runs(db_session, stranger.id, experiment_id=experiment.id).items == []


def test_config_edits_and_clones_do_not_mutate_existing_runs(db_session, owners):
    owner, stranger = owners
    experiment = make_experiment(db_session, owner, default_seed=-9223372036854775808,
                                 config={"Parallel_PoW_mining?": True})
    run = make_run(db_session, owner, experiment)
    updated = update_experiment(db_session, owner.id, experiment.id,
                                ExperimentUpdate(config={"NumOfFogNodes": 8}, notes="New template"))
    assert len(updated.config) == 23
    assert updated.config["NumOfFogNodes"] == 8
    assert updated.config["Parallel_PoW_mining"] is False  # config replaces the template
    db_session.expire_all()
    persisted_run = get_owned_run(db_session, owner.id, run.public_id)
    assert persisted_run.config["NumOfFogNodes"] == 5
    assert persisted_run.config["Parallel_PoW_mining"] is True
    cloned = clone_experiment(db_session, owner.id, experiment.id, ExperimentClone(name="Replica"))
    assert cloned.id != experiment.id and cloned.config == updated.config
    assert cloned.default_seed == -9223372036854775808 and cloned.notes == "New template"
    stranger_project = create_project(db_session, stranger.id, ProjectCreate(name="Private"))
    assert clone_experiment(db_session, owner.id, experiment.id,
                            ExperimentClone(project_id=stranger_project.id)) is None


def test_config_validation_uses_full_effective_placement_on_create_and_update(db_session, owners):
    owner, _ = owners
    project = create_project(db_session, owner.id, ProjectCreate(name="Study"))
    invalid = experiment_data(blockchain_placement=2, config={"NumOfMiners": 1})
    with pytest.raises(ValidationError):
        create_experiment(db_session, owner.id, project.id, invalid)
    assert list_owned_experiments(db_session, owner.id, project.id).items == []
    experiment = create_experiment(db_session, owner.id, project.id,
        experiment_data(config={"NumOfFogNodes": 8, "NumOfMiners": 2,
                                "Byzantine_nodes": 7, "number_of_each_miner_neighbours": 6}))
    with pytest.raises(ValidationError):
        update_experiment(db_session, owner.id, experiment.id, ExperimentUpdate(blockchain_placement=2))
    assert experiment.blockchain_placement == "1" and experiment.config["Byzantine_nodes"] == 7
    # Revalidate models too: Pydantic models can have been mutated after parsing.
    request = experiment_data()
    request.config.NumOfFogNodes = 1
    with pytest.raises(ValidationError):
        create_experiment(db_session, owner.id, project.id, request)


def test_server_generated_seeds_and_public_schema_do_not_expose_internal_ids(db_session, owners):
    owner, _ = owners
    experiment = make_experiment(db_session, owner)
    response = ExperimentResponse.model_validate(experiment)
    assert type(response.default_seed) is int
    assert -(2**63) <= response.default_seed < 2**63
    assert response.blockchain_function == 1 and response.blockchain_placement == 1
    assert response.consensus_algorithm == 1
    assert response.created_at.utcoffset().total_seconds() == 0
    assert "user_id" not in ProjectResponse.model_validate(experiment.project).model_dump()
    legacy = make_run(db_session, owner)
    payload = RunResponse.model_validate(legacy).model_dump(mode="json")
    assert UUID(payload["id"]) == legacy.public_id
    assert "user_id" not in payload and "public_id" not in payload
    assert payload["config"] == {"legacy": 3} and payload["seed"] is None


def test_run_pagination_is_stable_scoped_and_keeps_legacy_rows(db_session, owners):
    owner, stranger = owners
    experiment = make_experiment(db_session, owner)
    rows = [make_run(db_session, owner, experiment if i else None,
                     queued_at=datetime(2026, 1, 1, tzinfo=timezone.utc)) for i in range(5)]
    foreign_run = make_run(db_session, stranger)
    first = list_owned_runs(db_session, owner.id, limit=2)
    assert [item.id for item in first.items] == [rows[4].public_id, rows[3].public_id]
    assert first.next_cursor == rows[3].public_id
    make_run(db_session, owner, experiment)  # newer rows cannot shift the next page
    second = list_owned_runs(db_session, owner.id, limit=2, cursor=first.next_cursor)
    assert [item.id for item in second.items] == [rows[2].public_id, rows[1].public_id]
    last = list_owned_runs(db_session, owner.id, limit=2, cursor=second.next_cursor)
    assert [item.id for item in last.items] == [rows[0].public_id] and last.next_cursor is None
    for cursor in (foreign_run.public_id, uuid4()):
        assert list_owned_runs(db_session, owner.id, cursor=cursor).items == []
    assert list_owned_runs(db_session, owner.id, status="failed").items == []
    assert len(list_owned_runs(db_session, owner.id, experiment_id=experiment.id).items) == 5


@pytest.mark.parametrize("consumer", ["response", "pagination"])
def test_null_status_legacy_run_remains_readable_without_changing_history(db_session, owners, consumer):
    owner, stranger = owners
    legacy = make_run(db_session, owner, status=None)
    newer = make_run(db_session, owner, status="completed")
    db_session.expire_all()
    persisted = get_owned_run(db_session, owner.id, legacy.public_id)
    assert persisted.status is None
    if consumer == "response":
        response = RunResponse.model_validate(persisted)
    else:
        first = list_owned_runs(db_session, owner.id, limit=1)
        assert first.items[0].id == newer.public_id and first.next_cursor == newer.public_id
        last = list_owned_runs(db_session, owner.id, limit=1, cursor=first.next_cursor)
        assert len(last.items) == 1 and last.next_cursor is None
        response = last.items[0]
    assert response.id == legacy.public_id and response.status is None
    assert response.model_dump(mode="json")["status"] is None
    assert get_owned_run(db_session, owner.id, legacy.public_id).status is None
    assert get_owned_run(db_session, stranger.id, legacy.public_id) is None
    assert list_owned_runs(db_session, owner.id, status="completed").items[0].id == newer.public_id


@pytest.mark.parametrize("status", ["unknown", "null", "None", "", 0, True])
def test_run_status_filter_still_rejects_invalid_states(db_session, owners, status):
    owner, _ = owners
    with pytest.raises(ValueError):
        list_owned_runs(db_session, owner.id, status=status)


def test_project_and_experiment_pagination_break_timestamp_ties(db_session, owners):
    owner, stranger = owners
    projects = [create_project(db_session, owner.id, ProjectCreate(name="Duplicate")) for _ in range(3)]
    stamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for project in projects:
        project.created_at = stamp
    db_session.commit()
    expected = sorted((row.id for row in projects), reverse=True)
    first = list_owned_projects(db_session, owner.id, limit=2)
    assert [row.id for row in first.items] == expected[:2]
    assert [row.id for row in list_owned_projects(db_session, owner.id, limit=2, cursor=first.next_cursor).items] == expected[2:]
    experiments = [create_experiment(db_session, owner.id, projects[0].id, experiment_data()) for _ in range(3)]
    for experiment in experiments:
        experiment.created_at = stamp
    db_session.commit()
    expected = sorted((row.id for row in experiments), reverse=True)
    first = list_owned_experiments(db_session, owner.id, projects[0].id, limit=2)
    assert [row.id for row in first.items] == expected[:2]
    assert [row.id for row in list_owned_experiments(db_session, owner.id, projects[0].id, limit=2, cursor=first.next_cursor).items] == expected[2:]
    foreign = make_experiment(db_session, stranger)
    assert list_owned_projects(db_session, owner.id, cursor=foreign.project_id).items == []
    assert list_owned_experiments(db_session, owner.id, projects[0].id, cursor=foreign.id).items == []


@pytest.mark.parametrize("limit", [0, -1, 101, True, 1.5])
def test_list_limits_are_bounded(db_session, owners, limit):
    owner, _ = owners
    project = create_project(db_session, owner.id, ProjectCreate(name="Study"))
    for call in (lambda: list_owned_projects(db_session, owner.id, limit=limit),
                 lambda: list_owned_experiments(db_session, owner.id, project.id, limit=limit),
                 lambda: list_owned_runs(db_session, owner.id, limit=limit)):
        with pytest.raises(ValueError):
            call()


@pytest.mark.parametrize("bad", ["", "   ", "x" * 121])
def test_project_names_are_trimmed_nonempty_and_bounded(bad):
    with pytest.raises(ValidationError):
        ProjectCreate(name=bad)
    with pytest.raises(ValidationError):
        ProjectUpdate(name=bad)
    assert ProjectCreate(name=" Study ").name == "Study"


@pytest.mark.parametrize("changes", [
    {"name": None}, {"name": "x" * 161}, {"name": " "}, {"config": None},
    {"blockchain_function": True}, {"blockchain_placement": 1.0},
    {"blockchain_placement": 3}, {"consensus_algorithm": 7},
    {"default_seed": True}, {"default_seed": 2**63}, {"default_seed": -(2**63)-1},
    {"user_id": 1},
])
def test_experiment_schema_rejects_invalid_or_privileged_fields(changes):
    with pytest.raises(ValidationError):
        experiment_data(**changes)
    with pytest.raises(ValidationError):
        ExperimentUpdate(**changes)


def test_optional_text_can_be_cleared_but_required_project_fields_cannot():
    assert ProjectUpdate(description=None).model_dump(exclude_unset=True) == {"description": None}
    assert ExperimentUpdate(notes=None).model_dump(exclude_unset=True) == {"notes": None}
    with pytest.raises(ValidationError):
        ProjectUpdate(name=None)
