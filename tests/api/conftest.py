"""Isolated database and authenticated client fixtures for backend tests."""

import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


API_DIR = Path(__file__).resolve().parents[2] / "api"
sys.path.insert(0, str(API_DIR))
# Never let backend tests inherit a deployed database configuration.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["FRONTEND_URL"] = "http://localhost:3000"

import auth  # noqa: E402
import database  # noqa: E402
import models  # noqa: E402
from api.app_factory import create_app  # noqa: E402


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        database.Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session):
    app = create_app()

    def override_get_db():
        yield db_session

    app.dependency_overrides[database.get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def user_factory(db_session):
    def create_user(*, email=None, password="test-password", full_name="Test User"):
        user = models.User(
            email=email or f"user-{uuid4().hex}@example.com",
            hashed_password=auth.get_password_hash(password),
            full_name=full_name,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return create_user


@pytest.fixture
def auth_headers(user_factory):
    user = user_factory()
    token = auth.create_access_token(data={"sub": user.email})
    return {"Authorization": f"Bearer {token}"}
