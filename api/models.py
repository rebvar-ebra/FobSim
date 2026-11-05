from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime, default=utc_now)

    simulations = relationship("Simulation", back_populates="user")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    password_fingerprint = Column(String(64), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    function = Column(String)
    placement = Column(String)
    consensus = Column(String)
    status = Column(String)  # running, completed, stopped
    config = Column(JSON)
    started_at = Column(DateTime, default=utc_now)
    ended_at = Column(DateTime, nullable=True)

    # Summary stats
    blocks_mined = Column(Integer, default=0)
    avg_cpu = Column(Float, default=0)
    forks = Column(Integer, default=0)
    consistency = Column(Float, default=100.0) # Percentage
    latency = Column(Float, default=0.0)      # Average block time (sec)
    throughput = Column(Float, default=0.0)   # Transactions per second (TPS)
    energy_used = Column(Float, default=0.0)  # Estimated energy in kWh

    user = relationship("User", back_populates="simulations")
