"""Complete canonical configuration and the legacy engine serialization boundary.

Canonical defaults preserve the former API defaults, independently of the mutable
engine file. Numeric limits live in NUMERIC_BOUNDS; placement-dependent limits
are applied with ``model_validate(raw, context={"placement": placement})``.
Use validate_effective_config at persistence/launch boundaries to validate the
complete configuration with strict selectors and the hosted work budget.
"""

from collections.abc import Mapping
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationInfo, model_validator


# Canonical field -> exact Sim_parameters.json key. Both input normalization and
# engine output use this single mapping; persisted snapshots use the left side.
LEGACY_ENGINE_KEYS = {
    "NumOfFogNodes": "NumOfFogNodes",
    "num_of_users_per_fog_node": "num_of_users_per_fog_node",
    "NumOfTaskPerUser": "NumOfTaskPerUser",
    "NumOfMiners": "NumOfMiners",
    "number_of_each_miner_neighbours": "number_of_each_miner_neighbours",
    "numOfTXperBlock": "numOfTXperBlock",
    "puzzle_difficulty": "puzzle_difficulty",
    "poet_block_time": "poet_block_time",
    "Max_enduser_payment": "Max_enduser_payment",
    "miners_initial_wallet_value": "miners_initial_wallet_value",
    "mining_award": "mining_award",
    "delay_between_fog_nodes": "delay_between_fog_nodes",
    "delay_between_end_users": "delay_between_end_users",
    "Gossip_Activated": "Gossip_Activated",
    "Automatic_PoA_miners_authorization": "Automatic_PoA_miners_authorization?",
    "Parallel_PoW_mining": "Parallel_PoW_mining?",
    "Asymmetric_key_length": "Asymmetric_key_length",
    "Num_of_DPoS_delegates": "Num_of_DPoS_delegates",
    "STOR_PLC": "STOR_PLC(0=in the Fog,1=in the BC)",
    "Byzantine_nodes": "Byzantine_nodes",
    "Attack_type": "Attack_type",
    "Layer2_Rollup_Enabled": "Layer2_Rollup_Enabled",
    "Layer2_Batch_Size": "Layer2_Batch_Size",
}

# Inclusive service limits. Discrete domains are declared as Literal fields.
NUMERIC_BOUNDS = {
    "NumOfFogNodes": (1, 100),
    "num_of_users_per_fog_node": (1, 100),
    "NumOfTaskPerUser": (1, 1000),
    "NumOfMiners": (1, 100),
    "number_of_each_miner_neighbours": (0, 100),
    "numOfTXperBlock": (1, 10000),
    "puzzle_difficulty": (1, 3),
    "poet_block_time": (1, 3600),
    "Max_enduser_payment": (0, 1_000_000_000_000),
    "miners_initial_wallet_value": (0, 1_000_000_000_000),
    "mining_award": (0, 1_000_000_000_000),
    "delay_between_fog_nodes": (0, 3600),
    "delay_between_end_users": (0, 3600),
    "Num_of_DPoS_delegates": (1, 100),
    "Byzantine_nodes": (0, 100),
    "Layer2_Batch_Size": (1, 10000),
}

MAX_TOTAL_USERS = 500
MAX_TOTAL_TASKS = 5000
MAX_EXPECTED_BLOCKS = 1000
MAX_PARALLEL_POW_BLOCKS = 64


def _bounded(name: str, default: int):
    minimum, maximum = NUMERIC_BOUNDS[name]
    return Field(default=default, ge=minimum, le=maximum)


def require_integer(value: Any) -> int:
    """Keep Literal's equality matching from accepting booleans or floats."""
    if type(value) is not int:
        raise ValueError("must be an integer")
    return value


BlockchainFunction = Annotated[Literal[1, 2, 3, 4, 5], BeforeValidator(require_integer)]
BlockchainPlacement = Annotated[Literal[1, 2], BeforeValidator(require_integer)]
ConsensusAlgorithm = Annotated[Literal[1, 2, 3, 4, 5, 6, 8, 9, 10], BeforeValidator(require_integer)]


class SimulationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)

    NumOfFogNodes: int = _bounded("NumOfFogNodes", 5)
    num_of_users_per_fog_node: int = _bounded("num_of_users_per_fog_node", 5)
    NumOfTaskPerUser: int = _bounded("NumOfTaskPerUser", 5)
    NumOfMiners: int = _bounded("NumOfMiners", 4)
    number_of_each_miner_neighbours: int = _bounded("number_of_each_miner_neighbours", 3)
    numOfTXperBlock: int = _bounded("numOfTXperBlock", 5)
    puzzle_difficulty: int = _bounded("puzzle_difficulty", 2)
    poet_block_time: int = _bounded("poet_block_time", 1)
    Max_enduser_payment: int = _bounded("Max_enduser_payment", 100)
    miners_initial_wallet_value: int = _bounded("miners_initial_wallet_value", 1000)
    mining_award: int = _bounded("mining_award", 5)
    delay_between_fog_nodes: float = _bounded("delay_between_fog_nodes", 0)
    delay_between_end_users: float = _bounded("delay_between_end_users", 0)
    Gossip_Activated: bool = True
    Automatic_PoA_miners_authorization: bool = True
    Parallel_PoW_mining: bool = False
    Asymmetric_key_length: Annotated[Literal[512, 1024, 2048, 4096], BeforeValidator(require_integer)] = 512
    Num_of_DPoS_delegates: int = _bounded("Num_of_DPoS_delegates", 2)
    STOR_PLC: Annotated[Literal[0, 1], BeforeValidator(require_integer)] = 0
    Byzantine_nodes: int = _bounded("Byzantine_nodes", 0)
    Attack_type: Annotated[Literal[0, 1, 2], BeforeValidator(require_integer)] = 0
    Layer2_Rollup_Enabled: bool = False
    Layer2_Batch_Size: int = _bounded("Layer2_Batch_Size", 100)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_keys(cls, raw: Any) -> Any:
        if not isinstance(raw, Mapping):
            return raw
        normalized = dict(raw)
        for canonical, legacy in LEGACY_ENGINE_KEYS.items():
            if legacy == canonical or legacy not in normalized:
                continue
            value = normalized.pop(legacy)
            if canonical in normalized and (
                type(normalized[canonical]) is not type(value)
                or normalized[canonical] != value
            ):
                raise ValueError(f"Conflicting values for {canonical} and {legacy}")
            normalized[canonical] = value
        return normalized

    @model_validator(mode="after")
    def validate_placement_limits(self, info: ValidationInfo) -> "SimulationConfig":
        if info.context and "placement" in info.context:
            count = effective_miner_count(self, info.context["placement"])
            for field in ("Byzantine_nodes", "number_of_each_miner_neighbours", "Num_of_DPoS_delegates"):
                if getattr(self, field) > count:
                    raise ValueError(f"{field} cannot exceed the effective miner count ({count})")
        return self


class _EffectiveConfiguration(BaseModel):
    blockchain_function: BlockchainFunction
    blockchain_placement: BlockchainPlacement
    consensus_algorithm: ConsensusAlgorithm
    config: SimulationConfig

    @model_validator(mode="after")
    def validate_engine_work(self) -> "_EffectiveConfiguration":
        # Placement constraints precede selector-dependent engine preconditions.
        config = SimulationConfig.model_validate(
            self.config.model_dump(), context={"placement": self.blockchain_placement},
        )
        if self.blockchain_function == 3 and config.Max_enduser_payment < 1:
            raise ValueError("Payment/Trading requires Max_enduser_payment >= 1")
        if self.consensus_algorithm == 5 and effective_miner_count(config, self.blockchain_placement) < 2:
            raise ValueError("DPoS requires at least 2 effective miners")

        total_users = config.NumOfFogNodes * config.num_of_users_per_fog_node
        total_tasks = total_users * config.NumOfTaskPerUser
        # Match main.py: computational services uses one block per task.
        expected_blocks = total_tasks if self.blockchain_function == 2 else (
            total_tasks + config.numOfTXperBlock - 1
        ) // config.numOfTXperBlock
        if total_users > MAX_TOTAL_USERS:
            raise ValueError(f"total_users cannot exceed {MAX_TOTAL_USERS}")
        if total_tasks > MAX_TOTAL_TASKS:
            raise ValueError(f"total_tasks cannot exceed {MAX_TOTAL_TASKS}")
        if expected_blocks > MAX_EXPECTED_BLOCKS:
            raise ValueError(f"expected_blocks cannot exceed {MAX_EXPECTED_BLOCKS}")
        if (self.consensus_algorithm == 1 and config.Parallel_PoW_mining
                and expected_blocks > MAX_PARALLEL_POW_BLOCKS):
            raise ValueError(f"Parallel PoW expected_blocks cannot exceed {MAX_PARALLEL_POW_BLOCKS}")
        self.config = config
        return self


def validate_effective_config(
    config: Mapping[str, Any] | SimulationConfig, *, blockchain_function: int,
    blockchain_placement: int, consensus_algorithm: int,
) -> SimulationConfig:
    """Revalidate all inputs before saving a template or launching an engine run."""
    # A caller may have mutated a previously validated model; never trust it.
    raw = config.model_dump() if isinstance(config, BaseModel) else config
    return _EffectiveConfiguration(
        config=raw, blockchain_function=blockchain_function,
        blockchain_placement=blockchain_placement, consensus_algorithm=consensus_algorithm,
    ).config


def canonicalize_config(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Validate aliases and fill defaults, returning a complete JSON snapshot."""
    return SimulationConfig.model_validate(raw).model_dump(mode="json")


def to_engine_config(config: SimulationConfig) -> dict[str, Any]:
    """Serialize only the engine's exact keys, never canonical alias duplicates."""
    snapshot = config.model_dump(mode="json")
    return {legacy: snapshot[canonical] for canonical, legacy in LEGACY_ENGINE_KEYS.items()}


def effective_miner_count(config: SimulationConfig, placement: int | str) -> int:
    """Match main.py: Fog creates fog-node miners; End User creates NumOfMiners."""
    if not isinstance(placement, bool):
        if placement in (1, "Fog"):
            return config.NumOfFogNodes
        if placement in (2, "End User"):
            return config.NumOfMiners
    raise ValueError("placement must be 1 (Fog) or 2 (End User)")
