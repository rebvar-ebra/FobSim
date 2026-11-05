from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, JsonValue

from api.schemas import ResponseSchema
from api.schemas.experiments import Seed


RunStatus = Literal["queued", "running", "completed", "failed", "stopped", "interrupted"]


class RunResponse(ResponseSchema):
    id: UUID = Field(validation_alias="public_id")
    experiment_id: UUID | None
    seed: Seed | None
    engine_version: str | None
    # Legacy rows may have no recorded status; preserve that missing evidence.
    status: RunStatus | None
    function: str | None
    placement: str | None
    consensus: str | None
    # Legacy snapshots remain partial: serializing history must not invent inputs.
    config: dict[str, JsonValue] | None
    error_message: str | None
    queued_at: datetime | None
    started_at: datetime | None
    ended_at: datetime | None
    blocks_mined: int | None
    avg_cpu: float | None
    forks: int | None
    consistency: float | None
    latency: float | None
    throughput: float | None
    energy_used: float | None


class RunPage(ResponseSchema):
    items: list[RunResponse]
    next_cursor: UUID | None = None
