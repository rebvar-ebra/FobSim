from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BeforeValidator, Field, StringConstraints, field_validator

from api.config_schema import SimulationConfig, require_integer
from api.schemas import RequestSchema, ResponseSchema, UpdateSchema


ExperimentName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
BlockchainFunction = Annotated[Literal[1, 2, 3, 4, 5], BeforeValidator(require_integer)]
BlockchainPlacement = Annotated[Literal[1, 2], BeforeValidator(require_integer)]
ConsensusAlgorithm = Annotated[Literal[1, 2, 3, 4, 5, 6, 8, 9, 10], BeforeValidator(require_integer)]
Seed = Annotated[int, Field(strict=True, ge=-(2**63), le=2**63 - 1)]


class ExperimentCreate(RequestSchema):
    name: ExperimentName
    hypothesis: str | None = None
    notes: str | None = None
    blockchain_function: BlockchainFunction
    blockchain_placement: BlockchainPlacement
    consensus_algorithm: ConsensusAlgorithm
    config: SimulationConfig = Field(default_factory=SimulationConfig)
    default_seed: Seed | None = None


class ExperimentUpdate(UpdateSchema):
    nonnullable_fields = frozenset({
        "name", "blockchain_function", "blockchain_placement", "consensus_algorithm",
        "config", "default_seed",
    })
    name: ExperimentName | None = None
    hypothesis: str | None = None
    notes: str | None = None
    blockchain_function: BlockchainFunction | None = None
    blockchain_placement: BlockchainPlacement | None = None
    consensus_algorithm: ConsensusAlgorithm | None = None
    config: SimulationConfig | None = None
    default_seed: Seed | None = None


class ExperimentClone(RequestSchema):
    name: ExperimentName | None = None
    project_id: UUID | None = None


class ExperimentResponse(ResponseSchema):
    id: UUID
    project_id: UUID
    name: str
    hypothesis: str | None
    notes: str | None
    blockchain_function: BlockchainFunction
    blockchain_placement: BlockchainPlacement
    consensus_algorithm: ConsensusAlgorithm
    config: SimulationConfig
    default_seed: Seed
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_validator("blockchain_function", "blockchain_placement", "consensus_algorithm", mode="before")
    @classmethod
    def stored_selector(cls, value):
        # Existing model columns are String; only canonical decimal IDs are stored.
        return int(value) if isinstance(value, str) and value.isdecimal() else value


class ExperimentPage(ResponseSchema):
    items: list[ExperimentResponse]
    next_cursor: UUID | None = None
