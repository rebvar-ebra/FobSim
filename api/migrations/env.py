"""Migrate a supplied connection or the deployment's DATABASE_URL."""

import os

from alembic import context
from sqlalchemy import create_engine, pool

from database import Base
import models  # noqa: F401 -- register model metadata for future revisions


config = context.config
target_metadata = Base.metadata


def run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    # This baseline must inspect the database before deciding which DDL is safe.
    raise RuntimeError("The legacy-adopting baseline requires an online database connection.")

connection = config.attributes.get("connection")
if connection is not None:
    run_migrations(connection)
else:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(url, poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            run_migrations(connection)
    finally:
        engine.dispose()
