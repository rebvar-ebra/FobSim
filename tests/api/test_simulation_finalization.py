"""Exercise finalization through the executor with real persistence and analytics."""

import asyncio
from datetime import datetime, timezone
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import event
from sqlalchemy.orm import attributes, sessionmaker

import blockchain
import models
import server


@pytest.mark.parametrize(
    ("has_chains", "aware_start"),
    [(True, True), (False, True), (True, False)],
    ids=["aware-with-chain-metrics", "aware-without-chains", "sqlite-naive-with-chain-metrics"],
)
def test_executor_commits_final_status_and_metrics_for_run_timestamps(
    db_session, tmp_path, monkeypatch, capsys, has_chains, aware_start,
):
    started_at = datetime(2026, 11, 5, 12, tzinfo=timezone.utc)
    ended_at = datetime(2026, 11, 5, 13, tzinfo=timezone.utc)
    run = models.Simulation(
        status="running", started_at=started_at, consensus="Proof of Work (PoW)",
        config={"numOfTXperBlock": 10},
    )
    db_session.add(run)
    db_session.commit()
    run_id = run.id

    finalizer_sessions = sessionmaker(bind=db_session.get_bind())
    completion_times = []

    @event.listens_for(finalizer_sessions, "loaded_as_persistent")
    def restore_postgresql_style_start(session, instance):
        # SQLite discards timezone information. Restore the value a PostgreSQL
        # TIMESTAMPTZ loader supplies, keeping the query and persistence real.
        if isinstance(instance, models.Simulation) and aware_start:
            attributes.set_committed_value(
                instance, "started_at", instance.started_at.replace(tzinfo=timezone.utc),
            )

    @event.listens_for(finalizer_sessions, "before_flush")
    def capture_completion_time(session, flush_context, instances):
        for instance in session.dirty:
            if isinstance(instance, models.Simulation):
                completion_times.append(instance.ended_at)

    monkeypatch.setattr(server, "SessionLocal", finalizer_sessions)
    monkeypatch.setattr(models, "utc_now", lambda: ended_at)
    monkeypatch.setattr(blockchain, "data", {"NumOfFogNodes": 2})
    (tmp_path / "api").mkdir()
    monkeypatch.setattr(server, "__file__", str(tmp_path / "api" / "server.py"))
    temp_dir = tmp_path / "temporary"
    temp_dir.mkdir()
    if has_chains:
        (temp_dir / "miner_local_chain.json").write_text(json.dumps({
            "0": {"Header": {"hash": "genesis"}, "Body": {"timestamp": 100}},
            "1": {"Header": {"hash": "tip"}, "Body": {"timestamp": 110}},
        }))

    process = SimpleNamespace(
        returncode=0,
        stdin=SimpleNamespace(write=lambda data: None, drain=AsyncMock(), close=lambda: None),
        stdout=SimpleNamespace(readline=AsyncMock(side_effect=[b"Block proposed\n"] * 4 + [b""])),
        wait=AsyncMock(return_value=0),
    )
    monkeypatch.setattr(server.asyncio, "create_subprocess_exec", AsyncMock(return_value=process))
    monkeypatch.setattr(server, "simulation_running", True)
    monkeypatch.setattr(server, "simulation_output", [])
    monkeypatch.setattr(server, "simulation_process", None)

    asyncio.run(server.execute_simulation(1, 1, 1, run_id))

    # Query in another session so an uncommitted/failed finalizer cannot pass.
    with finalizer_sessions() as verification_session:
        saved = verification_session.get(models.Simulation, run_id)
        assert saved.status == "completed"
        assert saved.ended_at.replace(tzinfo=timezone.utc) == ended_at
        assert saved.blocks_mined == 2
        if has_chains:
            assert saved.forks == 1
            assert saved.consistency == 100.0
            assert saved.throughput == 2.0
            assert saved.latency == 5.0
            assert saved.energy_used == 1.1  # 100 W base + 1,000 W PoW, for one hour.
    assert completion_times == [ended_at]
    assert completion_times[0].utcoffset().total_seconds() == 0
    assert "Failed to update final sim status" not in capsys.readouterr().out
