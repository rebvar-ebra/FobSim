"""Paginated owner run history, including archived/deleted historical scopes."""

from uuid import UUID

from fastapi import APIRouter

from api.routes import CurrentUser, Database, PageLimit, require_found
from api.schemas.runs import RunPage, RunStatus
from api.services import experiments, projects, runs


router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("", response_model=RunPage)
def list_runs(db: Database, current_user: CurrentUser, project_id: UUID | None = None,
              experiment_id: UUID | None = None, status: RunStatus | None = None,
              cursor: UUID | None = None, limit: PageLimit = 50):
    if project_id is not None:
        require_found(projects.get_owned_project(db, current_user.id, project_id, include_hidden=True))
    if experiment_id is not None:
        require_found(experiments.get_owned_experiment(db, current_user.id, experiment_id, include_hidden=True))
    return runs.list_owned_runs(db, current_user.id, project_id=project_id,
                                experiment_id=experiment_id, status=status, cursor=cursor, limit=limit)
