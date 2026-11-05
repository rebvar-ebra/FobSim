"""Adopt legacy FobSim data and add the research workspace.

Revision ID: 20261105_01
Revises: None
"""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "20261105_01"
down_revision = None
branch_labels = None
depends_on = None


def ensure_index(table, name, columns, *, unique=False):
    if name not in {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table)}:
        op.create_index(name, table, columns, unique=unique)


def upgrade():
    bind = op.get_bind()
    postgres = bind.dialect.name == "postgresql"
    uuid_default = sa.text("gen_random_uuid()") if postgres else None
    tables = set(sa.inspect(bind).get_table_names())

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("email", sa.String),
            sa.Column("hashed_password", sa.String),
            sa.Column("full_name", sa.String),
            sa.Column("created_at", sa.DateTime),
        )
    ensure_index("users", "ix_users_id", ["id"])
    ensure_index("users", "ix_users_email", ["email"], unique=True)

    if "password_reset_tokens" not in tables:
        op.create_table(
            "password_reset_tokens",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
            sa.Column("token_hash", sa.String(64), nullable=False),
            sa.Column("password_fingerprint", sa.String(64), nullable=False),
            sa.Column("expires_at", sa.DateTime, nullable=False),
            sa.Column("used_at", sa.DateTime, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False),
        )
    for column in ("id", "user_id", "expires_at"):
        ensure_index("password_reset_tokens", f"ix_password_reset_tokens_{column}", [column])
    ensure_index("password_reset_tokens", "ix_password_reset_tokens_token_hash", ["token_hash"], unique=True)

    if "research_projects" not in tables:
        op.create_table(
            "research_projects",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, server_default=uuid_default),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column("description", sa.Text),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    ensure_index("research_projects", "ix_research_projects_user_id", ["user_id"])

    if "experiments" not in tables:
        op.create_table(
            "experiments",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, server_default=uuid_default),
            sa.Column("project_id", sa.Uuid(as_uuid=True), sa.ForeignKey("research_projects.id"), nullable=False),
            sa.Column("name", sa.String(160), nullable=False),
            sa.Column("hypothesis", sa.Text),
            sa.Column("notes", sa.Text),
            sa.Column("blockchain_function", sa.String, nullable=False),
            sa.Column("blockchain_placement", sa.String, nullable=False),
            sa.Column("consensus_algorithm", sa.String, nullable=False),
            sa.Column("config", sa.JSON, nullable=False),
            sa.Column("default_seed", sa.BigInteger, nullable=False),
            sa.Column("archived_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    ensure_index("experiments", "ix_experiments_project_id", ["project_id"])

    if "simulations" not in tables:
        op.create_table(
            "simulations",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
            sa.Column("function", sa.String),
            sa.Column("placement", sa.String),
            sa.Column("consensus", sa.String),
            sa.Column("status", sa.String),
            sa.Column("config", sa.JSON),
            sa.Column("started_at", sa.DateTime(timezone=True)),
            sa.Column("ended_at", sa.DateTime(timezone=True)),
            sa.Column("blocks_mined", sa.Integer),
            sa.Column("avg_cpu", sa.Float),
            sa.Column("forks", sa.Integer),
            sa.Column("consistency", sa.Float),
            sa.Column("latency", sa.Float),
            sa.Column("throughput", sa.Float),
            sa.Column("energy_used", sa.Float),
        )

    existing_columns = {column["name"] for column in sa.inspect(bind).get_columns("simulations")}
    new_columns = (
        sa.Column("public_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("experiment_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("seed", sa.BigInteger, nullable=True),
        sa.Column("engine_version", sa.String, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("logs_text", sa.Text, nullable=True),
        sa.Column("results_json", sa.JSON, nullable=True),
        sa.Column("artifact_manifest", sa.JSON, nullable=True),
    )
    for column in new_columns:
        if column.name not in existing_columns:
            if column.name == "experiment_id" and bind.dialect.name == "sqlite":
                # SQLite supports an inline FK on ADD COLUMN; a separate ALTER
                # CONSTRAINT would require rebuilding this populated legacy table.
                op.execute("ALTER TABLE simulations ADD COLUMN experiment_id CHAR(32) REFERENCES experiments(id)")
            else:
                op.add_column("simulations", column)

    simulations = sa.table(
        "simulations", sa.column("id", sa.Integer),
        sa.column("public_id", sa.Uuid(as_uuid=True)), sa.column("status", sa.String),
    )
    # Generate a different UUID for every historical record without inventing
    # missing seeds/configuration/logs or changing legacy integer identities.
    missing_ids = bind.execute(sa.select(simulations.c.id).where(simulations.c.public_id.is_(None))).scalars().all()
    for run_id in missing_ids:
        bind.execute(simulations.update().where(simulations.c.id == run_id).values(public_id=uuid4()))
    for old, new in (("running", "interrupted"), ("completed", "completed"), ("stopped", "stopped")):
        bind.execute(simulations.update().where(sa.func.lower(sa.func.trim(simulations.c.status)) == old).values(status=new))

    if postgres:
        # Legacy timestamps were naive UTC. A plain type cast would interpret
        # them in the deployment's session zone and silently shift old runs.
        for column in sa.inspect(bind).get_columns("simulations"):
            if column["name"] in {"started_at", "ended_at"} and not column["type"].timezone:
                op.alter_column(
                    "simulations", column["name"], existing_type=column["type"],
                    type_=sa.DateTime(timezone=True),
                    postgresql_using=f"{column['name']} AT TIME ZONE 'UTC'",
                )
        op.alter_column("simulations", "public_id", existing_type=sa.Uuid(), nullable=False, server_default=uuid_default)
        foreign_keys = sa.inspect(bind).get_foreign_keys("simulations")
        if not any(fk["constrained_columns"] == ["experiment_id"] for fk in foreign_keys):
            op.create_foreign_key("fk_simulations_experiment_id", "simulations", "experiments", ["experiment_id"], ["id"])
    # SQLite adoption intentionally keeps the added UUID column nullable at the
    # DDL level: changing it would recreate the legacy table. Application inserts
    # still generate non-null UUIDs, and the unique index protects all values.
    ensure_index("simulations", "ix_simulations_id", ["id"])
    ensure_index("simulations", "ix_simulations_public_id", ["public_id"], unique=True)
    ensure_index("simulations", "ix_simulations_experiment_id", ["experiment_id"])


def downgrade():
    raise RuntimeError("This data-preserving baseline cannot be downgraded safely. Restore a verified backup instead.")
