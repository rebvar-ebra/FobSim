"""Shared HTTP dependencies and error mapping for research routes."""

import json
from contextlib import contextmanager
from typing import Annotated

from fastapi import Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session

import auth
import models
from database import get_db


Database = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[models.User, Depends(auth.get_current_user)]
PageLimit = Annotated[int, Query(ge=1, le=100)]


def require_found(resource):
    if resource is None:
        raise HTTPException(status_code=404, detail="Not found")
    return resource


@contextmanager
def validate_write():
    """Service validation includes the stored template and placement context."""
    try:
        yield
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=json.loads(exc.json())) from exc
