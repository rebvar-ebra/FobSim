"""Exercise the initial migration against real empty and pre-Alembic databases."""

from datetime import datetime, timezone
import os
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models


API_DIR = Path(__file__).resolve().parents[2] / "api"


def upgrade(connection):
    config = Config(str(API_DIR / "alembic.ini"))
    config.attributes["connection"] = connection
    command.upgrade(config, "head")


@pytest.fixture
def connection(tmp_path):
    engine = sa.create_engine(sa.URL.create("sqlite", database=str(tmp_path / "migration.db")))
    with engine.connect() as connection:
        connection.execute(sa.text("PRAGMA foreign_keys=ON"))
        connection.commit()
        yield connection
    engine.dispose()


def create_legacy_schema(connection):
    # Intentionally independent of current model metadata: this is the deployed schema.
    for statement in (
        """CREATE TABLE users (
            id INTEGER PRIMARY KEY, email VARCHAR UNIQUE, hashed_password VARCHAR,
            full_name VARCHAR, created_at DATETIME)""",
        """CREATE TABLE password_reset_tokens (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
            token_hash VARCHAR(64) NOT NULL UNIQUE, password_fingerprint VARCHAR(64) NOT NULL,
            expires_at DATETIME NOT NULL, used_at DATETIME, created_at DATETIME NOT NULL)""",
        """CREATE TABLE simulations (
            id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
            function VARCHAR, placement VARCHAR, consensus VARCHAR, status VARCHAR,
            config JSON, started_at DATETIME, ended_at DATETIME, blocks_mined INTEGER,
            avg_cpu FLOAT, forks INTEGER, consistency FLOAT, latency FLOAT,
            throughput FLOAT, energy_used FLOAT)""",
    ):
        if connection.dialect.name == "postgresql":
            statement = statement.replace("DATETIME", "TIMESTAMP")
        connection.execute(sa.text(statement))
    connection.commit()


def test_upgrade_empty_database_to_head(connection):
    upgrade(connection)

    assert set(sa.inspect(connection).get_table_names()) == {
        "alembic_version", "users", "password_reset_tokens", "simulations",
        "research_projects", "experiments",
    }
    assert connection.scalar(sa.text("SELECT version_num FROM alembic_version")) == "20261105_01"
    assert {column["name"] for column in sa.inspect(connection).get_columns("simulations")} >= {
        "id", "public_id", "experiment_id", "seed", "engine_version", "error_message",
        "queued_at", "logs_text", "results_json", "artifact_manifest",
    }
    assert {tuple(fk["constrained_columns"]) for fk in sa.inspect(connection).get_foreign_keys("simulations")} == {
        ("user_id",), ("experiment_id",),
    }
    # A second upgrade is a no-op, including after data has been written.
    connection.execute(sa.text("INSERT INTO users (id, email) VALUES (1, 'empty@example.test')"))
    connection.commit()
    upgrade(connection)
    assert connection.scalar(sa.text("SELECT email FROM users WHERE id=1")) == "empty@example.test"


def test_upgrade_legacy_database_preserves_rows_and_backfills_public_ids(connection):
    create_legacy_schema(connection)
    connection.execute(sa.text("""INSERT INTO users VALUES
        (7, 'legacy@example.test', 'unchanged-hash', 'Legacy User', '2020-01-02 03:04:05')"""))
    connection.execute(sa.text("""INSERT INTO password_reset_tokens VALUES
        (11, 7, 'token-hash', 'password-fingerprint', '2030-01-01', NULL, '2020-01-01')"""))
    for run_id, status in ((21, "running"), (22, "completed"), (23, "stopped"), (24, " RUNNING ")):
        connection.execute(sa.text("""INSERT INTO simulations
            (id, user_id, function, placement, consensus, status, config, started_at,
             ended_at, blocks_mined, avg_cpu, forks, consistency, latency, throughput, energy_used)
            VALUES (:id, 7, 'storage', 'fog', 'PoW', :status, '{"nodes": 3}',
             '2020-01-02 03:04:05', NULL, 12, 1.5, 2, 98.5, 0.2, 5.5, 0.1)"""),
            {"id": run_id, "status": status})
    before_user = connection.execute(sa.text("SELECT * FROM users")).all()
    before_reset = connection.execute(sa.text("SELECT * FROM password_reset_tokens")).all()
    before_runs = connection.execute(sa.text("SELECT id, user_id, config, started_at, blocks_mined, avg_cpu FROM simulations ORDER BY id")).all()
    table_roots = connection.execute(sa.text("SELECT name, rootpage FROM sqlite_master WHERE type='table' AND name IN ('users', 'password_reset_tokens', 'simulations') ORDER BY name")).all()
    connection.commit()

    upgrade(connection)

    assert connection.execute(sa.text("SELECT * FROM users")).all() == before_user
    assert connection.execute(sa.text("SELECT * FROM password_reset_tokens")).all() == before_reset
    assert connection.execute(sa.text("SELECT id, user_id, config, started_at, blocks_mined, avg_cpu FROM simulations ORDER BY id")).all() == before_runs
    assert connection.execute(sa.text("SELECT name, rootpage FROM sqlite_master WHERE type='table' AND name IN ('users', 'password_reset_tokens', 'simulations') ORDER BY name")).all() == table_roots
    rows = connection.execute(sa.text("SELECT id, public_id, status, experiment_id, seed, logs_text, results_json FROM simulations ORDER BY id")).all()
    assert [row.status for row in rows] == ["interrupted", "completed", "stopped", "interrupted"]
    assert len({UUID(row.public_id) for row in rows}) == 4
    assert all(row.experiment_id is None and row.seed is None and row.logs_text is None and row.results_json is None for row in rows)
    with pytest.raises(IntegrityError), connection.begin_nested():
        connection.execute(sa.text("UPDATE simulations SET public_id=:public_id WHERE id=22"), {"public_id": rows[0].public_id})
    with pytest.raises(IntegrityError), connection.begin_nested():
        connection.execute(sa.text("UPDATE simulations SET experiment_id='00000000000000000000000000000001' WHERE id=21"))
    connection.commit()

    upgrade(connection)
    assert connection.execute(sa.text("SELECT id, public_id, status, experiment_id, seed, logs_text, results_json FROM simulations ORDER BY id")).all() == rows


def test_upgrade_adopts_empty_legacy_tables(connection):
    create_legacy_schema(connection)
    upgrade(connection)
    with Session(connection) as session:
        user = models.User(email="owner@example.test")
        project = models.ResearchProject(user=user, name="Study")
        experiment = models.Experiment(
            project=project, name="Baseline", blockchain_function="storage",
            blockchain_placement="fog", consensus_algorithm="PoW", config={"nodes": 3},
            default_seed=9223372036854775807,
        )
        run = models.Simulation(user=user, experiment=experiment, status="queued", seed=-9223372036854775808)
        session.add(run)
        session.commit()
        assert isinstance(project.id, UUID) and isinstance(experiment.id, UUID)
        assert isinstance(run.public_id, UUID)
        assert run.seed == -9223372036854775808
        assert experiment.default_seed == 9223372036854775807
        assert project.experiments == [experiment]
        assert experiment.simulations == [run]
        assert user.projects == [project]
        assert project.created_at is not None and experiment.updated_at is not None


def test_new_research_timestamps_use_aware_utc():
    assert models.utc_now().utcoffset().total_seconds() == 0
    for model, fields in (
        (models.ResearchProject, ("created_at", "updated_at", "deleted_at")),
        (models.Experiment, ("created_at", "updated_at", "archived_at")),
        (models.Simulation, ("queued_at", "started_at", "ended_at")),
    ):
        assert all(model.__table__.c[field].type.timezone for field in fields)


@pytest.mark.skipif(not os.environ.get("FOBSIM_TEST_POSTGRES_URL"), reason="optional isolated PostgreSQL migration check")
def test_postgresql_adoption_preserves_legacy_utc_and_uses_server_uuid_defaults():
    engine = sa.create_engine(os.environ["FOBSIM_TEST_POSTGRES_URL"])
    schema = f"fobsim_migration_{uuid4().hex}"
    with engine.connect() as connection:
        connection.execute(sa.schema.CreateSchema(schema))
        connection.execute(sa.text(f'SET search_path TO "{schema}"'))
        connection.commit()
        try:
            create_legacy_schema(connection)
            connection.execute(sa.text("INSERT INTO users (id, email) VALUES (7, 'legacy@example.test')"))
            connection.execute(sa.text("""INSERT INTO password_reset_tokens VALUES
                (11, 7, 'token-hash', 'fingerprint', '2030-01-01', NULL, '2020-01-01')"""))
            connection.execute(sa.text("""INSERT INTO simulations (id, user_id, status, started_at, ended_at)
                VALUES (21, 7, 'completed', '2020-01-02 03:04:05', '2020-01-02 04:05:06'),
                       (22, 7, 'running', '2020-01-03 05:06:07', NULL)"""))
            old_reset = connection.execute(sa.text("SELECT * FROM password_reset_tokens")).all()
            old_tables = connection.execute(sa.text("""SELECT oid, relname FROM pg_class
                WHERE relnamespace=current_schema()::regnamespace AND relkind='r' ORDER BY relname""")).all()
            # Conversion must interpret the old values as UTC, regardless of the session zone.
            connection.execute(sa.text("SET TIME ZONE 'Europe/Berlin'"))
            connection.commit()

            upgrade(connection)

            assert connection.execute(sa.text("""SELECT oid, relname FROM pg_class
                WHERE relnamespace=current_schema()::regnamespace
                AND relname IN ('users','simulations','password_reset_tokens') ORDER BY relname""")).all() == old_tables
            assert connection.execute(sa.text("SELECT * FROM password_reset_tokens")).all() == old_reset
            rows = connection.execute(sa.text("SELECT id, public_id, status, started_at, ended_at FROM simulations ORDER BY id")).all()
            assert rows[0].started_at == datetime(2020, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
            assert rows[0].ended_at == datetime(2020, 1, 2, 4, 5, 6, tzinfo=timezone.utc)
            assert rows[1].started_at == datetime(2020, 1, 3, 5, 6, 7, tzinfo=timezone.utc)
            assert rows[1].ended_at is None and rows[1].status == "interrupted"
            assert all(isinstance(row.public_id, UUID) for row in rows)
            assert len({row.public_id for row in rows}) == 2
            columns = {column["name"]: column for column in sa.inspect(connection).get_columns("simulations")}
            assert all(columns[field]["type"].timezone for field in ("queued_at", "started_at", "ended_at"))
            assert not columns["public_id"]["nullable"]
            assert isinstance(connection.scalar(sa.text("INSERT INTO simulations (id, status) VALUES (23, 'running') RETURNING public_id")), UUID)
            project_id = connection.scalar(sa.text("""INSERT INTO research_projects
                (user_id, name, created_at, updated_at) VALUES (7, 'Study', now(), now()) RETURNING id"""))
            assert isinstance(project_id, UUID)
            experiment_id = connection.scalar(sa.text("""INSERT INTO experiments
                (project_id, name, blockchain_function, blockchain_placement, consensus_algorithm,
                 config, default_seed, created_at, updated_at)
                VALUES (:project, 'Baseline', 'storage', 'fog', 'PoW', '{}', 1, now(), now()) RETURNING id"""), {"project": project_id})
            assert isinstance(experiment_id, UUID)
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(sa.text("UPDATE simulations SET public_id=NULL WHERE id=21"))
            connection.commit()

            upgrade(connection)
            assert connection.scalar(sa.text("SELECT status FROM simulations WHERE id=23")) == "running"
        finally:
            connection.rollback()
            connection.execute(sa.schema.DropSchema(schema, cascade=True))
            connection.commit()
    engine.dispose()
