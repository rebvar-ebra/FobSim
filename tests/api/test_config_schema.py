"""Canonical snapshots, engine compatibility, and safe simulation inputs."""

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from api.config_schema import (
    SimulationConfig,
    canonicalize_config,
    effective_miner_count,
    to_engine_config,
)
import models
import server


DEFAULT_ENGINE_CONFIG = {
    "NumOfFogNodes": 5,
    "num_of_users_per_fog_node": 5,
    "NumOfTaskPerUser": 5,
    "NumOfMiners": 4,
    "number_of_each_miner_neighbours": 3,
    "numOfTXperBlock": 5,
    "puzzle_difficulty": 2,
    "poet_block_time": 1,
    "Max_enduser_payment": 100,
    "miners_initial_wallet_value": 1000,
    "mining_award": 5,
    "delay_between_fog_nodes": 0,
    "delay_between_end_users": 0,
    "Gossip_Activated": True,
    "Automatic_PoA_miners_authorization?": True,
    "Parallel_PoW_mining?": False,
    "Asymmetric_key_length": 512,
    "Num_of_DPoS_delegates": 2,
    "STOR_PLC(0=in the Fog,1=in the BC)": 0,
    "Byzantine_nodes": 0,
    "Attack_type": 0,
    "Layer2_Rollup_Enabled": False,
    "Layer2_Batch_Size": 100,
}


@pytest.mark.parametrize(
    ("legacy", "canonical", "value"),
    [
        ("Automatic_PoA_miners_authorization?", "Automatic_PoA_miners_authorization", False),
        ("Parallel_PoW_mining?", "Parallel_PoW_mining", True),
        ("STOR_PLC(0=in the Fog,1=in the BC)", "STOR_PLC", 1),
    ],
)
def test_legacy_alias_and_api_name_produce_identical_canonical_snapshots(legacy, canonical, value):
    from_legacy = canonicalize_config({legacy: value})
    assert from_legacy == canonicalize_config({canonical: value})
    assert from_legacy[canonical] == value
    assert legacy not in from_legacy
    assert to_engine_config(SimulationConfig.model_validate(from_legacy))[legacy] == value


def test_default_snapshot_contains_every_engine_setting():
    assert to_engine_config(SimulationConfig()) == DEFAULT_ENGINE_CONFIG
    canonical = canonicalize_config({"NumOfFogNodes": 7})
    assert len(canonical) == 23
    assert canonical["NumOfFogNodes"] == 7
    assert canonical["numOfTXperBlock"] == 5
    assert not any("?" in key or "(" in key for key in canonical)


def test_checked_in_engine_configuration_round_trips_without_losing_fields():
    raw = json.loads((Path(__file__).resolve().parents[2] / "Sim_parameters.json").read_text())
    assert to_engine_config(SimulationConfig.model_validate(canonicalize_config(raw))) == raw


def test_default_fog_run_accepts_actual_shipped_configuration():
    shipped = json.loads((Path(__file__).resolve().parents[2] / "Sim_parameters.json").read_text())
    request = server.RunSimulation()
    effective = request.effective_config(shipped)
    assert request.blockchain_placement == 1
    assert effective.number_of_each_miner_neighbours <= effective.NumOfFogNodes
    assert to_engine_config(effective) == shipped


def test_conflicting_aliases_and_unknown_settings_are_rejected():
    with pytest.raises(ValidationError):
        canonicalize_config({"Parallel_PoW_mining?": True, "Parallel_PoW_mining": False})
    with pytest.raises(ValidationError):
        canonicalize_config({"NumOfFogNode": 8})
    assert canonicalize_config({"Parallel_PoW_mining?": True, "Parallel_PoW_mining": True})[
        "Parallel_PoW_mining"
    ] is True


@pytest.mark.parametrize(
    "canonical", ["Automatic_PoA_miners_authorization", "Parallel_PoW_mining"],
)
@pytest.mark.parametrize(("canonical_value", "legacy_value"), [(1, True), (0, False), (True, 1), (False, 0)])
def test_duplicate_boolean_aliases_reject_integer_boolean_pairs(canonical, canonical_value, legacy_value):
    with pytest.raises(ValidationError):
        canonicalize_config({canonical: canonical_value, f"{canonical}?": legacy_value})


@pytest.mark.parametrize(
    "canonical", ["Automatic_PoA_miners_authorization", "Parallel_PoW_mining"],
)
@pytest.mark.parametrize("value", [True, False])
def test_duplicate_boolean_aliases_accept_matching_booleans(canonical, value):
    snapshot = canonicalize_config({canonical: value, f"{canonical}?": value})
    assert snapshot[canonical] is value


@pytest.mark.parametrize(
    "canonical", ["Automatic_PoA_miners_authorization", "Parallel_PoW_mining"],
)
@pytest.mark.parametrize(("canonical_value", "legacy_value"), [(True, False), (False, True)])
def test_duplicate_boolean_aliases_reject_unequal_booleans(canonical, canonical_value, legacy_value):
    with pytest.raises(ValidationError):
        canonicalize_config({canonical: canonical_value, f"{canonical}?": legacy_value})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("NumOfFogNodes", 0),
        ("NumOfFogNodes", 101),
        ("num_of_users_per_fog_node", 0),
        ("num_of_users_per_fog_node", 101),
        ("NumOfTaskPerUser", 0),
        ("NumOfTaskPerUser", 1001),
        ("NumOfMiners", 0),
        ("NumOfMiners", 101),
        ("number_of_each_miner_neighbours", -1),
        ("number_of_each_miner_neighbours", 101),
        ("numOfTXperBlock", 0),
        ("numOfTXperBlock", 10001),
        ("puzzle_difficulty", 0),
        ("puzzle_difficulty", 65),
        ("poet_block_time", 0),
        ("poet_block_time", 3601),
        ("Max_enduser_payment", -1),
        ("Max_enduser_payment", 1000000000001),
        ("miners_initial_wallet_value", -1),
        ("miners_initial_wallet_value", 1000000000001),
        ("mining_award", -1),
        ("mining_award", 1000000000001),
        ("delay_between_fog_nodes", -0.1),
        ("delay_between_fog_nodes", 3601),
        ("delay_between_end_users", -0.1),
        ("delay_between_end_users", 3601),
        ("Asymmetric_key_length", 511),
        ("Asymmetric_key_length", 4097),
        ("Asymmetric_key_length", 513),
        ("Num_of_DPoS_delegates", 0),
        ("Num_of_DPoS_delegates", 101),
        ("STOR_PLC", -1),
        ("STOR_PLC", 2),
        ("Byzantine_nodes", -1),
        ("Byzantine_nodes", 101),
        ("Attack_type", -1),
        ("Attack_type", 3),
        ("Layer2_Batch_Size", 0),
        ("Layer2_Batch_Size", 10001),
        ("NumOfFogNodes", 2.5),
        ("delay_between_fog_nodes", float("inf")),
        ("Gossip_Activated", 1),
        ("Automatic_PoA_miners_authorization", "true"),
        ("Parallel_PoW_mining", 0),
        ("Layer2_Rollup_Enabled", "false"),
    ],
)
def test_unsafe_numeric_values_are_rejected(field, value):
    with pytest.raises(ValidationError):
        canonicalize_config({field: value})


def test_delays_preserve_fractional_seconds():
    assert to_engine_config(SimulationConfig(delay_between_fog_nodes=0.25))[
        "delay_between_fog_nodes"
    ] == 0.25


@pytest.mark.parametrize(
    ("field", "low", "high"),
    [
        ("NumOfFogNodes", 1, 100),
        ("NumOfMiners", 1, 100),
        ("num_of_users_per_fog_node", 1, 100),
        ("NumOfTaskPerUser", 1, 1000),
        ("number_of_each_miner_neighbours", 0, 100),
        ("numOfTXperBlock", 1, 10000),
        ("puzzle_difficulty", 1, 64),
        ("poet_block_time", 1, 3600),
        ("Max_enduser_payment", 0, 1000000000000),
        ("miners_initial_wallet_value", 0, 1000000000000),
        ("mining_award", 0, 1000000000000),
        ("delay_between_fog_nodes", 0, 3600),
        ("delay_between_end_users", 0, 3600),
        ("Num_of_DPoS_delegates", 1, 100),
        ("Byzantine_nodes", 0, 100),
        ("Layer2_Batch_Size", 1, 10000),
    ],
)
def test_numeric_limits_are_inclusive(field, low, high):
    assert canonicalize_config({field: low})[field] == low
    assert canonicalize_config({field: high})[field] == high


@pytest.mark.parametrize("key_length", [512, 1024, 2048, 4096])
def test_supported_key_lengths_are_accepted(key_length):
    assert canonicalize_config({"Asymmetric_key_length": key_length})["Asymmetric_key_length"] == key_length


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("Asymmetric_key_length", True), ("Asymmetric_key_length", False),
        ("Asymmetric_key_length", 512.0), ("Asymmetric_key_length", 1024.0),
        ("Asymmetric_key_length", 2048.0), ("Asymmetric_key_length", 4096.0),
        ("STOR_PLC", True), ("STOR_PLC", False),
        ("STOR_PLC", 0.0), ("STOR_PLC", 1.0),
        ("Attack_type", True), ("Attack_type", False),
        ("Attack_type", 0.0), ("Attack_type", 1.0), ("Attack_type", 2.0),
    ],
)
def test_discrete_config_fields_reject_booleans_and_floats(field, value):
    with pytest.raises(ValidationError):
        canonicalize_config({field: value})


@pytest.mark.parametrize(("field", "value"), [("STOR_PLC", 0), ("STOR_PLC", 1),
                                             ("Attack_type", 0), ("Attack_type", 1), ("Attack_type", 2)])
def test_discrete_config_fields_accept_approved_integers(field, value):
    snapshot = canonicalize_config({field: value})
    assert snapshot[field] == value
    assert type(snapshot[field]) is int


@pytest.mark.parametrize("field", ["blockchain_function", "blockchain_placement", "consensus_algorithm"])
@pytest.mark.parametrize("value", [True, False, 1.0, 2.0])
def test_run_identifiers_reject_booleans_and_floats(field, value):
    with pytest.raises(ValidationError):
        server.RunSimulation.model_validate({field: value})


@pytest.mark.parametrize(
    ("field", "value"),
    [("blockchain_function", 1), ("blockchain_function", 2), ("blockchain_function", 3),
     ("blockchain_function", 4), ("blockchain_function", 5),
     ("blockchain_placement", 1), ("blockchain_placement", 2),
     ("consensus_algorithm", 1), ("consensus_algorithm", 2), ("consensus_algorithm", 3),
     ("consensus_algorithm", 4), ("consensus_algorithm", 5), ("consensus_algorithm", 6),
     ("consensus_algorithm", 8), ("consensus_algorithm", 9), ("consensus_algorithm", 10)],
)
def test_run_identifiers_accept_all_approved_integers(field, value):
    request = server.RunSimulation.model_validate({field: value})
    assert getattr(request, field) == value
    assert type(getattr(request, field)) is int


@pytest.mark.parametrize(("placement", "expected"), [(1, 4), ("Fog", 4), (2, 8), ("End User", 8)])
def test_effective_miner_count_uses_the_selected_layer(placement, expected):
    assert effective_miner_count(SimulationConfig(NumOfFogNodes=4, NumOfMiners=8), placement) == expected


@pytest.mark.parametrize("placement", [0, 3, "Cloud"])
def test_unknown_placements_are_rejected(placement):
    with pytest.raises(ValueError):
        effective_miner_count(SimulationConfig(), placement)


@pytest.mark.parametrize("field", ["Byzantine_nodes", "number_of_each_miner_neighbours", "Num_of_DPoS_delegates"])
@pytest.mark.parametrize("placement", [1, 2, "Fog", "End User"])
def test_counts_cannot_exceed_the_effective_miner_count(field, placement):
    fog = placement in (1, "Fog")
    raw = {"NumOfFogNodes": 4 if fog else 8, "NumOfMiners": 8 if fog else 4, field: 5}
    with pytest.raises(ValidationError, match=field):
        SimulationConfig.model_validate(raw, context={"placement": placement})
    raw[field] = 4
    assert getattr(SimulationConfig.model_validate(raw, context={"placement": placement}), field) == 4


@pytest.fixture
def config_file(tmp_path, monkeypatch):
    (tmp_path / "api").mkdir()
    monkeypatch.setattr(server, "__file__", str(tmp_path / "api" / "server.py"))
    path = tmp_path / "Sim_parameters.json"
    path.write_text(json.dumps({**DEFAULT_ENGINE_CONFIG, "numOfTXperBlock": 17}))
    return path


def test_config_update_merges_aliases_and_writes_only_engine_keys(client, config_file):
    response = client.post("/api/config", json={"Parallel_PoW_mining": True, "STOR_PLC": 1})
    assert response.status_code == 200
    written = json.loads(config_file.read_text())
    assert written == {**DEFAULT_ENGINE_CONFIG, "numOfTXperBlock": 17, "Parallel_PoW_mining?": True,
                       "STOR_PLC(0=in the Fog,1=in the BC)": 1}
    assert response.json()["config"] == written
    assert client.get("/api/config").json() == written


def test_run_persists_complete_effective_canonical_snapshot(
    client, db_session, auth_headers, config_file, monkeypatch,
):
    monkeypatch.setattr(server, "execute_simulation", AsyncMock())
    monkeypatch.setattr(server, "simulation_running", False)
    response = client.post("/api/run", headers=auth_headers, json={
        "blockchain_placement": 2,
        "config": {"Parallel_PoW_mining?": True},
    })
    assert response.status_code == 200
    saved = db_session.get(models.Simulation, response.json()["simulation_id"])
    assert saved.config == canonicalize_config({**DEFAULT_ENGINE_CONFIG, "numOfTXperBlock": 17,
                                               "Parallel_PoW_mining?": True})
    assert json.loads(config_file.read_text())["Parallel_PoW_mining?"] is True


def test_run_without_overrides_persists_file_snapshot(client, db_session, auth_headers, config_file, monkeypatch):
    monkeypatch.setattr(server, "execute_simulation", AsyncMock())
    monkeypatch.setattr(server, "simulation_running", False)
    response = client.post("/api/run", headers=auth_headers, json={"blockchain_placement": 1})
    assert response.status_code == 200
    saved = db_session.get(models.Simulation, response.json()["simulation_id"])
    assert saved.config == canonicalize_config({**DEFAULT_ENGINE_CONFIG, "numOfTXperBlock": 17})


@pytest.mark.parametrize("use_ui_overrides", [False, True], ids=["default-request", "current-ui-request"])
def test_default_fog_launch_uses_actual_shipped_configuration(
    client, db_session, auth_headers, tmp_path, monkeypatch, use_ui_overrides,
):
    shipped_path = Path(__file__).resolve().parents[2] / "Sim_parameters.json"
    shipped_text = shipped_path.read_text()
    shipped = json.loads(shipped_text)
    payload = {}
    if use_ui_overrides:
        payload = {
            "blockchain_function": 1,
            "blockchain_placement": 1,
            "consensus_algorithm": 1,
            "config": {field: shipped[field] for field in (
                "NumOfFogNodes", "NumOfMiners", "numOfTXperBlock", "puzzle_difficulty",
                "Byzantine_nodes", "Attack_type", "Layer2_Rollup_Enabled", "Layer2_Batch_Size",
            )},
        }

    # Validate the real shipped file before isolating the route's config writes.
    effective = server.RunSimulation.model_validate(payload).effective_config(shipped)
    assert effective.number_of_each_miner_neighbours <= effective.NumOfFogNodes
    assert to_engine_config(effective) == shipped

    (tmp_path / "api").mkdir()
    monkeypatch.setattr(server, "__file__", str(tmp_path / "api" / "server.py"))
    engine_path = tmp_path / "Sim_parameters.json"
    engine_path.write_text(shipped_text)
    monkeypatch.setattr(server, "execute_simulation", AsyncMock())
    monkeypatch.setattr(server, "simulation_running", False)

    response = client.post("/api/run", headers=auth_headers, json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "started"
    saved = db_session.get(models.Simulation, response.json()["simulation_id"])
    assert saved.placement == "Fog"
    assert saved.config["NumOfFogNodes"] == shipped["NumOfFogNodes"]
    assert saved.config["number_of_each_miner_neighbours"] == shipped["number_of_each_miner_neighbours"]
    assert json.loads(engine_path.read_text()) == shipped
    assert shipped_path.read_text() == shipped_text


def test_run_without_overrides_writes_default_filled_engine_snapshot(
    client, db_session, auth_headers, config_file, monkeypatch,
):
    config_file.write_text(json.dumps({"NumOfFogNodes": 8}))
    monkeypatch.setattr(server, "execute_simulation", AsyncMock())
    monkeypatch.setattr(server, "simulation_running", False)
    response = client.post("/api/run", headers=auth_headers, json={})
    assert response.status_code == 200
    assert json.loads(config_file.read_text()) == {**DEFAULT_ENGINE_CONFIG, "NumOfFogNodes": 8}
    saved = db_session.get(models.Simulation, response.json()["simulation_id"])
    assert saved.config["NumOfFogNodes"] == 8
    assert saved.config["numOfTXperBlock"] == 5


@pytest.mark.parametrize("field", ["Byzantine_nodes", "number_of_each_miner_neighbours", "Num_of_DPoS_delegates"])
@pytest.mark.parametrize("placement", [1, 2])
def test_run_validates_merged_configuration_before_writing_or_saving(
    client, db_session, auth_headers, config_file, monkeypatch, field, placement,
):
    monkeypatch.setattr(server, "simulation_running", False)
    original = config_file.read_text()
    response = client.post("/api/run", headers=auth_headers, json={
        "blockchain_placement": placement,
        "config": {
            "NumOfFogNodes": 2 if placement == 1 else 10,
            "NumOfMiners": 10 if placement == 1 else 2,
            "number_of_each_miner_neighbours": 2,
            "Num_of_DPoS_delegates": 2,
            field: 3,
        },
    })
    assert response.status_code == 422
    assert field in str(response.json()["detail"])
    assert db_session.query(models.Simulation).count() == 0
    assert config_file.read_text() == original


@pytest.mark.parametrize(
    "identifiers",
    [{"blockchain_function": 0}, {"blockchain_function": 6}, {"blockchain_placement": 3},
     {"consensus_algorithm": 7}, {"consensus_algorithm": 11}],
)
def test_run_rejects_unknown_engine_identifiers(client, auth_headers, config_file, identifiers):
    response = client.post("/api/run", headers=auth_headers, json=identifiers)
    assert response.status_code == 422
