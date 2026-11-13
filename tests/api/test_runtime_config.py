"""Runtime security boundaries exercised through app construction and HTTP."""

import os
from pathlib import Path
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from jose import JWTError, jwt

import auth
from api.app_factory import create_app


@pytest.fixture(autouse=True)
def runtime_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "disposable-runtime-test-key-8a72b09cf6")
    monkeypatch.setenv("FRONTEND_URL", "https://research.example.test")


@pytest.mark.parametrize("secret", [
    None, "", " \t\n", "super-secret-fobsim-key-change-me", "secret",
    "changeme", "change-me", "your-secret-key", "development-secret", "test-secret",
    "default-secret", "your-secret-key-here", "change-me-in-production", "replace-me",
])
def test_production_rejects_missing_blank_or_placeholder_jwt_secret(monkeypatch, secret):
    if secret is None:
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    else:
        monkeypatch.setenv("JWT_SECRET_KEY", secret)
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        create_app()


def test_unspecified_environment_also_rejects_placeholder_secret(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv("JWT_SECRET_KEY", "development-secret")
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        create_app()


def test_nonproduction_accepts_explicit_development_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("JWT_SECRET_KEY", "development-secret")
    with TestClient(create_app()) as client:
        assert client.get("/").status_code == 200
    token = auth.create_access_token({"sub": "researcher@example.test"})
    assert jwt.decode(token, "development-secret", algorithms=["HS256"])["sub"] == "researcher@example.test"


def test_access_tokens_use_configured_key_and_reject_a_different_key():
    token = auth.create_access_token({"sub": "researcher@example.test"})
    assert jwt.decode(token, "disposable-runtime-test-key-8a72b09cf6", algorithms=["HS256"])["sub"] == "researcher@example.test"
    with pytest.raises(JWTError):
        jwt.decode(token, "another-disposable-test-key", algorithms=["HS256"])


@pytest.mark.parametrize("origin,allowed", [
    ("https://research.example.test", True),
    ("https://attacker.example.test", False),
    ("https://research.example.test.attacker.test", False),
    ("http://localhost:3000", False),
    ("https://fobsim-frontend.onrender.com", False),
])
def test_only_configured_origin_receives_credentialed_cors(origin, allowed):
    with TestClient(create_app()) as client:
        response = client.options("/api/projects", headers={
            "Origin": origin,
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "authorization,content-type",
        })
        actual = client.get("/", headers={"Origin": origin})
    if allowed:
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
        assert response.headers["access-control-allow-credentials"] == "true"
        assert "PATCH" in response.headers["access-control-allow-methods"]
        assert actual.headers["access-control-allow-origin"] == origin
    else:
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers
        assert "access-control-allow-origin" not in actual.headers


@pytest.mark.parametrize("origin", [None, "", " ", "*", "https://*.example.test",
    "https://one.test,https://two.test", "https://one.test https://two.test",
    "https://one.test/path", "https://one.test/", "https://one.test?query=1",
    "https://user@one.test", "file://one.test", "https://one.test#fragment",
])
def test_production_requires_one_explicit_frontend_origin(monkeypatch, origin):
    if origin is None:
        monkeypatch.delenv("FRONTEND_URL", raising=False)
    else:
        monkeypatch.setenv("FRONTEND_URL", origin)
    with pytest.raises(RuntimeError, match="FRONTEND_URL"):
        create_app()


def test_deployed_app_startup_does_not_create_schema(tmp_path):
    environment = os.environ.copy()
    environment["DATABASE_URL"] = f"sqlite:///{tmp_path / 'unmigrated.db'}"
    result = subprocess.run(
        [sys.executable, "-c", """
import sys
sys.path.insert(0, 'api')
from fastapi.testclient import TestClient
from sqlalchemy import inspect
import server
with TestClient(server.app) as client:
    assert client.get('/').status_code == 200
assert inspect(server.engine).get_table_names() == []
"""],
        cwd=Path(__file__).resolve().parents[2],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
