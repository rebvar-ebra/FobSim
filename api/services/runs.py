from uuid import UUID

from sqlalchemy.orm import Session

import models
from api.schemas.runs import RunPage, RunResponse, RunStatus
from api.services import validate_limit


QUEUED = "queued"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
STOPPED = "stopped"
INTERRUPTED = "interrupted"
ACTIVE_RUN_STATUSES = frozenset({QUEUED, RUNNING})
TERMINAL_RUN_STATUSES = frozenset({COMPLETED, FAILED, STOPPED, INTERRUPTED})
RUN_STATUSES = ACTIVE_RUN_STATUSES | TERMINAL_RUN_STATUSES


def get_owned_run(db: Session, owner_id: int, run_id: UUID) -> models.Simulation | None:
    return db.query(models.Simulation).filter(
        models.Simulation.user_id == owner_id, models.Simulation.public_id == run_id,
    ).first()


def list_owned_runs(db: Session, owner_id: int, *, project_id: UUID | None = None,
                    experiment_id: UUID | None = None, status: RunStatus | None = None,
                    cursor: UUID | None = None, limit: int = 50) -> RunPage:
    validate_limit(limit)
    if status is not None and status not in RUN_STATUSES:
        raise ValueError("Unknown run status")
    query = db.query(models.Simulation).filter(models.Simulation.user_id == owner_id)
    if project_id is not None or experiment_id is not None:
        # Keep history visible after deletion/archive, while checking the parent owner too.
        query = query.join(models.Experiment).join(models.ResearchProject).filter(
            models.ResearchProject.user_id == owner_id,
        )
        if project_id is not None:
            query = query.filter(models.Experiment.project_id == project_id)
        if experiment_id is not None:
            query = query.filter(models.Experiment.id == experiment_id)
    if status is not None:
        query = query.filter(models.Simulation.status == status)
    if cursor is not None:
        anchor = query.filter(models.Simulation.public_id == cursor).first()
        if anchor is None:
            return RunPage(items=[])
        query = query.filter(models.Simulation.id < anchor.id)
    rows = query.order_by(models.Simulation.id.desc()).limit(limit + 1).all()
    return RunPage(
        items=[RunResponse.model_validate(row) for row in rows[:limit]],
        next_cursor=rows[limit - 1].public_id if len(rows) > limit else None,
    )
