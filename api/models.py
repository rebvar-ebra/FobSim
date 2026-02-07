from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    simulations = relationship("Simulation", back_populates="user")

class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    function = Column(String)
    placement = Column(String)
    consensus = Column(String)
    status = Column(String)  # running, completed, stopped
    config = Column(JSON)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Summary stats
    blocks_mined = Column(Integer, default=0)
    avg_cpu = Column(Float, default=0)

    user = relationship("User", back_populates="simulations")
