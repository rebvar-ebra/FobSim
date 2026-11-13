from secrets import randbits
from uuid import uuid4

from sqlalchemy import BigInteger, Column, Integer, String, Float, JSON, ForeignKey, DateTime, Text, Uuid
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


def utc_now():
    return datetime.now(timezone.utc)


def legacy_utc_now():
    """Keep the pre-existing naive timestamp contract for auth/reset records."""
    return utc_now().replace(tzinfo=None)


def random_seed():
    return randbits(64) - (1 << 63)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime, default=legacy_utc_now)

    simulations = relationship("Simulation", back_populates="user")
    projects = relationship("ResearchProject", back_populates="user")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    password_fingerprint = Column(String(64), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=legacy_utc_now, nullable=False)


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="projects")
    experiments = relationship("Experiment", back_populates="project")


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("research_projects.id"), nullable=False, index=True)
    name = Column(String(160), nullable=False)
    hypothesis = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    blockchain_function = Column(String, nullable=False)
    blockchain_placement = Column(String, nullable=False)
    consensus_algorithm = Column(String, nullable=False)
    config = Column(JSON, nullable=False)
    default_seed = Column(BigInteger, default=random_seed, nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("ResearchProject", back_populates="experiments")
    simulations = relationship("Simulation", back_populates="experiment")

class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(Uuid(as_uuid=True), default=uuid4, nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    experiment_id = Column(Uuid(as_uuid=True), ForeignKey("experiments.id"), nullable=True, index=True)
    seed = Column(BigInteger, nullable=True)
    engine_version = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    function = Column(String)
    placement = Column(String)
    consensus = Column(String)
    status = Column(String)  # queued, running, completed, failed, stopped, interrupted
    config = Column(JSON)
    queued_at = Column(DateTime(timezone=True), default=utc_now, nullable=True)
    started_at = Column(DateTime(timezone=True), default=utc_now)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    logs_text = Column(Text, nullable=True)
    results_json = Column(JSON, nullable=True)
    artifact_manifest = Column(JSON, nullable=True)

    # Summary stats
    blocks_mined = Column(Integer, default=0)
    avg_cpu = Column(Float, default=0)
    forks = Column(Integer, default=0)
    consistency = Column(Float, default=100.0) # Percentage
    latency = Column(Float, default=0.0)      # Average block time (sec)
    throughput = Column(Float, default=0.0)   # Transactions per second (TPS)
    energy_used = Column(Float, default=0.0)  # Estimated energy in kWh

    user = relationship("User", back_populates="simulations")
    experiment = relationship("Experiment", back_populates="simulations")
