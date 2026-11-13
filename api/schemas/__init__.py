"""Shared public schema rules; internal database identifiers stay private."""

from datetime import datetime, timezone
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class RequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UpdateSchema(RequestSchema):
    nonnullable_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def reject_explicit_nulls(self):
        for name in self.model_fields_set & self.nonnullable_fields:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class ResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @field_validator("*", mode="after")
    @classmethod
    def utc_timestamps(cls, value):
        # SQLite drops timezone metadata on read; all research timestamps are UTC.
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return value
