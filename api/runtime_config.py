"""Read deployment security settings explicitly, without import-time caching."""

from dataclasses import dataclass, field
import os
from urllib.parse import urlsplit


_PLACEHOLDER_SECRETS = {
    "super-secret-fobsim-key-change-me", "secret", "secret-key", "default",
    "changeme", "change-me", "change_me", "your-secret-key", "your_secret_key",
    "development-secret", "dev-secret", "test-secret", "development", "test",
    "default-secret", "your-secret-key-here", "change-me-in-production", "replace-me",
}


@dataclass(frozen=True)
class RuntimeConfig:
    jwt_secret_key: str = field(repr=False)
    frontend_origin: str


def load_runtime_config() -> RuntimeConfig:
    environment = os.environ.get("APP_ENV", "production").strip().lower()
    if environment not in {"production", "development", "test"}:
        raise RuntimeError("APP_ENV must be production, development, or test.")

    secret = os.environ.get("JWT_SECRET_KEY", "")
    if not secret.strip() or (
        environment == "production" and secret.strip().lower() in _PLACEHOLDER_SECRETS
    ):
        raise RuntimeError("JWT_SECRET_KEY must be explicitly configured with a non-placeholder secret.")

    origin = os.environ.get("FRONTEND_URL", "")
    try:
        parsed = urlsplit(origin)
        valid_origin = (
            parsed.scheme in {"http", "https"}
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and not parsed.path
            and not parsed.query
            and not parsed.fragment
            and origin == f"{parsed.scheme}://{parsed.netloc}"
            and not any(character.isspace() or character in "*,\\" for character in origin)
        )
        # Accessing port also rejects malformed/out-of-range ports.
        parsed.port
    except ValueError:
        valid_origin = False
    if not valid_origin:
        raise RuntimeError("FRONTEND_URL must be one exact HTTP(S) origin without a path or wildcard.")

    return RuntimeConfig(jwt_secret_key=secret, frontend_origin=origin)
