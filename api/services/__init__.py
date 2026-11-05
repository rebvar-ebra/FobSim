"""Owner-scoped persistence services using caller-provided database sessions."""

from sqlalchemy import and_, or_


def validate_limit(limit: int) -> None:
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer between 1 and 100")


def paginate_created(query, model, page_type, response_type, *, cursor, limit):
    """Keyset pagination; the supplied query already includes owner/visibility filters."""
    validate_limit(limit)
    if cursor is not None:
        anchor = query.filter(model.id == cursor).first()
        if anchor is None:
            return page_type(items=[])
        query = query.filter(or_(
            model.created_at < anchor.created_at,
            and_(model.created_at == anchor.created_at, model.id < anchor.id),
        ))
    rows = query.order_by(model.created_at.desc(), model.id.desc()).limit(limit + 1).all()
    return page_type(
        items=[response_type.model_validate(row) for row in rows[:limit]],
        next_cursor=rows[limit - 1].id if len(rows) > limit else None,
    )
