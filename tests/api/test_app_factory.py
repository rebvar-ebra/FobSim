import pytest

from api.app_factory import create_app


def test_create_app_registers_health_and_auth_routes(client, auth_headers):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "FobSim API Server"

    paths = client.get("/openapi.json").json()["paths"]
    assert {
        "/api/auth/signup",
        "/api/auth/login",
        "/api/auth/forgot-password",
        "/api/auth/reset-password",
        "/api/auth/me",
    } <= paths.keys()
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers=auth_headers).status_code == 200
    assert create_app() is not client.app


@pytest.mark.parametrize("iteration", [1, 2])
def test_client_uses_isolated_database(client, user_factory, iteration):
    # Both invocations start fresh, even though the previous one committed a user.
    credentials = {"username": "isolated@example.com", "password": "test-password"}
    assert client.post("/api/auth/login", data=credentials).status_code == 400

    user = user_factory(email=credentials["username"])
    login = client.post("/api/auth/login", data=credentials)
    assert login.status_code == 200
    profile = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert profile.status_code == 200
    assert profile.json()["id"] == user.id
    assert profile.json()["email"] == "isolated@example.com"
