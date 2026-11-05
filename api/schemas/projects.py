from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import StringConstraints

from api.schemas import RequestSchema, ResponseSchema, UpdateSchema


ProjectName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class ProjectCreate(RequestSchema):
    name: ProjectName
    description: str | None = None


class ProjectUpdate(UpdateSchema):
    nonnullable_fields = frozenset({"name"})
    name: ProjectName | None = None
    description: str | None = None


class ProjectResponse(ResponseSchema):
    id: UUID
    name: str
    description: str | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ProjectPage(ResponseSchema):
    items: list[ProjectResponse]
    next_cursor: UUID | None = None
