"""Authenticated project resources; persistence lives in owner-scoped services."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response

from api.routes import CurrentUser, Database, PageLimit, require_found
from api.schemas.projects import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectPage
from api.services import projects


router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(data: ProjectCreate, db: Database, current_user: CurrentUser):
    return projects.create_project(db, current_user.id, data)


@router.get("", response_model=ProjectPage)
def list_projects(db: Database, current_user: CurrentUser,
                  cursor: UUID | None = None, limit: PageLimit = 50):
    return projects.list_owned_projects(db, current_user.id, cursor=cursor, limit=limit)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: UUID, db: Database, current_user: CurrentUser):
    return require_found(projects.get_owned_project(db, current_user.id, project_id))


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: UUID, data: ProjectUpdate, db: Database, current_user: CurrentUser):
    return require_found(projects.update_project(db, current_user.id, project_id, data))


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: UUID, db: Database, current_user: CurrentUser):
    try:
        require_found(projects.delete_project(db, current_user.id, project_id))
    except projects.ActiveRunsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(status_code=204)
