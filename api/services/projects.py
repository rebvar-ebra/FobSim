from uuid import UUID

from sqlalchemy.orm import Session

import models
from api.schemas.projects import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectPage
from api.services import paginate_created
from api.services.runs import ACTIVE_RUN_STATUSES


class ActiveRunsError(ValueError):
    """A project cannot be deleted while any of its runs are queued or running."""


def _owned_projects(db: Session, owner_id: int):
    return db.query(models.ResearchProject).filter(
        models.ResearchProject.user_id == owner_id,
        models.ResearchProject.deleted_at.is_(None),
    )


def get_owned_project(db: Session, owner_id: int, project_id: UUID) -> models.ResearchProject | None:
    return _owned_projects(db, owner_id).filter(models.ResearchProject.id == project_id).first()


def list_owned_projects(db: Session, owner_id: int, *, cursor: UUID | None = None, limit: int = 50) -> ProjectPage:
    return paginate_created(_owned_projects(db, owner_id), models.ResearchProject,
                            ProjectPage, ProjectResponse, cursor=cursor, limit=limit)


def create_project(db: Session, owner_id: int, data: ProjectCreate) -> models.ResearchProject:
    data = ProjectCreate.model_validate(data.model_dump())
    row = models.ResearchProject(user_id=owner_id, **data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_project(db: Session, owner_id: int, project_id: UUID, data: ProjectUpdate) -> models.ResearchProject | None:
    row = get_owned_project(db, owner_id, project_id)
    if row is None:
        return None
    changes = ProjectUpdate.model_validate(data.model_dump(exclude_unset=True)).model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(row, field, value)
    row.updated_at = models.utc_now()
    db.commit()
    db.refresh(row)
    return row


def delete_project(db: Session, owner_id: int, project_id: UUID) -> models.ResearchProject | None:
    row = get_owned_project(db, owner_id, project_id)
    if row is None:
        return None
    active = db.query(models.Simulation).join(models.Experiment).join(models.ResearchProject).filter(
        models.ResearchProject.id == project_id,
        models.ResearchProject.user_id == owner_id,
        models.Simulation.user_id == owner_id,
        models.Simulation.status.in_(ACTIVE_RUN_STATUSES),
    ).first()
    if active is not None:
        raise ActiveRunsError("Project has queued or running runs")
    row.deleted_at = row.updated_at = models.utc_now()
    db.commit()
    db.refresh(row)
    return row
