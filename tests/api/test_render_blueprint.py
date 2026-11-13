from pathlib import Path

import yaml


def test_backend_blueprint_provisions_a_persistent_jwt_secret():
    """Existing Blueprint services must not depend on creation-only prompts."""
    blueprint_path = Path(__file__).resolve().parents[2] / "render.yaml"
    blueprint = yaml.safe_load(blueprint_path.read_text(encoding="utf-8"))

    backend = next(
        service
        for service in blueprint["services"]
        if service["name"] == "fobsim-backend"
    )
    jwt_secret = next(
        variable
        for variable in backend["envVars"]
        if variable["key"] == "JWT_SECRET_KEY"
    )

    assert jwt_secret.get("generateValue") is True
    assert "value" not in jwt_secret
    assert "sync" not in jwt_secret
