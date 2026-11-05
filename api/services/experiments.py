from uuid import UUID

from sqlalchemy.orm import Session

import models
from api.config_schema import SimulationConfig
from api.schemas.experiments import (
    ExperimentCreate, ExperimentUpdate, ExperimentClone, ExperimentResponse, ExperimentPage,
)
from api.services import paginate_created
from api.services.projects import get_owned_project


SELECTOR_FIELDS = frozenset({"blockchain_function", "blockchain_placement", "consensus_algorithm"})


def _owned_experiments(db: Session, owner_id: int):
    return db.query(models.Experiment).join(models.ResearchProject).filter(
        models.ResearchProject.user_id == owner_id,
        models.ResearchProject.deleted_at.is_(None),
        models.Experiment.archived_at.is_(None),
    )


def get_owned_experiment(db: Session, owner_id: int, experiment_id: UUID) -> models.Experiment | None:
    return _owned_experiments(db, owner_id).filter(models.Experiment.id == experiment_id).first()


def list_owned_experiments(db: Session, owner_id: int, project_id: UUID, *,
                           cursor: UUID | None = None, limit: int = 50) -> ExperimentPage:
    query = _owned_experiments(db, owner_id).filter(models.Experiment.project_id == project_id)
    return paginate_created(query, models.Experiment, ExperimentPage, ExperimentResponse,
                            cursor=cursor, limit=limit)


def _validated_snapshot(raw, placement):
    return SimulationConfig.model_validate(raw, context={"placement": placement}).model_dump(mode="json")


def create_experiment(db: Session, owner_id: int, project_id: UUID, data: ExperimentCreate) -> models.Experiment | None:
    if get_owned_project(db, owner_id, project_id) is None:
        return None
    data = ExperimentCreate.model_validate(data.model_dump())
    values = data.model_dump(exclude={"default_seed"})
    values["config"] = _validated_snapshot(values["config"], data.blockchain_placement)
    for field in SELECTOR_FIELDS:
        values[field] = str(values[field])
    if data.default_seed is not None:
        values["default_seed"] = data.default_seed
    row = models.Experiment(project_id=project_id, **values)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_experiment(db: Session, owner_id: int, experiment_id: UUID, data: ExperimentUpdate) -> models.Experiment | None:
    """Update metadata; a supplied config replaces the template and fills defaults."""
    row = get_owned_experiment(db, owner_id, experiment_id)
    if row is None:
        return None
    changes = ExperimentUpdate.model_validate(data.model_dump(exclude_unset=True)).model_dump(exclude_unset=True)
    placement = changes.get("blockchain_placement", int(row.blockchain_placement))
    # Validate before mutating the ORM row, including placement-only edits.
    changes["config"] = _validated_snapshot(changes.get("config", row.config), placement)
    for field, value in changes.items():
        setattr(row, field, str(value) if field in SELECTOR_FIELDS else value)
    row.updated_at = models.utc_now()
    db.commit()
    db.refresh(row)
    return row


def archive_experiment(db: Session, owner_id: int, experiment_id: UUID) -> models.Experiment | None:
    row = get_owned_experiment(db, owner_id, experiment_id)
    if row is None:
        return None
    row.archived_at = row.updated_at = models.utc_now()
    db.commit()
    db.refresh(row)
    return row


def clone_experiment(db: Session, owner_id: int, experiment_id: UUID, data: ExperimentClone) -> models.Experiment | None:
    row = get_owned_experiment(db, owner_id, experiment_id)
    if row is None:
        return None
    data = ExperimentClone.model_validate(data.model_dump())
    return create_experiment(db, owner_id, data.project_id or row.project_id, ExperimentCreate(
        name=data.name if data.name is not None else f"{row.name[:155]} copy",
        hypothesis=row.hypothesis, notes=row.notes,
        blockchain_function=int(row.blockchain_function), blockchain_placement=int(row.blockchain_placement),
        consensus_algorithm=int(row.consensus_algorithm), config=row.config, default_seed=row.default_seed,
    ))
