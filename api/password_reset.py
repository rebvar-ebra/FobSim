import hashlib
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone


DEFAULT_RESET_EXPIRY_MINUTES = 30
RESET_TOKEN_BYTES = 32


class PasswordResetRequestLimiter:
    def __init__(
        self,
        per_ip_limit: int,
        global_limit: int,
        window_seconds: int,
    ):
        self.per_ip_limit = per_ip_limit
        self.global_limit = global_limit
        self.window_seconds = window_seconds
        self._global_events: deque[tuple[float, str]] = deque()
        self._ip_events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, ip_address: str, now: float | None = None) -> bool:
        timestamp = time.monotonic() if now is None else now
        cutoff = timestamp - self.window_seconds

        with self._lock:
            while self._global_events and self._global_events[0][0] <= cutoff:
                expired_at, expired_ip = self._global_events.popleft()
                ip_events = self._ip_events[expired_ip]
                if ip_events and ip_events[0] == expired_at:
                    ip_events.popleft()
                if not ip_events:
                    self._ip_events.pop(expired_ip, None)

            ip_events = self._ip_events[ip_address]
            if (
                len(ip_events) >= self.per_ip_limit
                or len(self._global_events) >= self.global_limit
            ):
                if not ip_events:
                    self._ip_events.pop(ip_address, None)
                return False

            ip_events.append(timestamp)
            self._global_events.append((timestamp, ip_address))
            return True


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def password_reset_expiry() -> datetime:
    return utc_now() + timedelta(minutes=DEFAULT_RESET_EXPIRY_MINUTES)


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(RESET_TOKEN_BYTES)


def hash_password_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def password_fingerprint(password_hash: str) -> str:
    return hashlib.sha256(password_hash.encode("utf-8")).hexdigest()
