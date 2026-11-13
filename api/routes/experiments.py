"""Experiment templates, metadata, cloning, and archive endpoints."""

from uuid import UUID

from fastapi import APIRouter, Response

from api.routes import CurrentUser, Database, PageLimit, require_found, validate_write
from api.schemas.experiments import (
    ExperimentCreate, ExperimentUpdate, ExperimentClone, ExperimentResponse, ExperimentPage,
)
from api.services import experiments, projects


router = APIRouter(prefix="/api", tags=["experiments"])


@router.post("/projects/{project_id}/experiments", response_model=ExperimentResponse, status_code=201)
def create_experiment(project_id: UUID, data: ExperimentCreate, db: Database, current_user: CurrentUser):
    with validate_write():
        return require_found(experiments.create_experiment(db, current_user.id, project_id, data))


@router.get("/projects/{project_id}/experiments", response_model=ExperimentPage)
def list_experiments(project_id: UUID, db: Database, current_user: CurrentUser,
                     cursor: UUID | None = None, limit: PageLimit = 50):
    require_found(projects.get_owned_project(db, current_user.id, project_id))
    return experiments.list_owned_experiments(db, current_user.id, project_id, cursor=cursor, limit=limit)


@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(experiment_id: UUID, db: Database, current_user: CurrentUser):
    return require_found(experiments.get_owned_experiment(db, current_user.id, experiment_id))


@router.patch("/experiments/{experiment_id}", response_model=ExperimentResponse)
def update_experiment(experiment_id: UUID, data: ExperimentUpdate, db: Database, current_user: CurrentUser):
    with validate_write():
        return require_found(experiments.update_experiment(db, current_user.id, experiment_id, data))


@router.delete("/experiments/{experiment_id}", status_code=204)
def archive_experiment(experiment_id: UUID, db: Database, current_user: CurrentUser):
    require_found(experiments.archive_experiment(db, current_user.id, experiment_id))
    return Response(status_code=204)


@router.post("/experiments/{experiment_id}/clone", response_model=ExperimentResponse, status_code=201)
def clone_experiment(experiment_id: UUID, data: ExperimentClone, db: Database, current_user: CurrentUser):
    with validate_write():
        return require_found(experiments.clone_experiment(db, current_user.id, experiment_id, data))
