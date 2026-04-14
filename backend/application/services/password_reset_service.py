from __future__ import annotations

import secrets
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional


class PasswordResetService:
    """
    Manages password-reset tokens.

    Tokens are stored in memory (sufficient for a single-process app).
    Each token expires after TTL_MINUTES and is single-use.
    """

    TTL_MINUTES = 60

    def __init__(self) -> None:
        self._tokens: dict[str, dict] = {}  # token -> {user_id, email, expires_at}
        self._lock = threading.Lock()

    def create_token(self, user_id: str, email: str) -> str:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.TTL_MINUTES)
        with self._lock:
            # Invalidate any existing token for this user
            self._tokens = {
                t: v for t, v in self._tokens.items() if v["user_id"] != user_id
            }
            self._tokens[token] = {
                "user_id": user_id,
                "email": email,
                "expires_at": expires_at,
            }
        return token

    def consume_token(self, token: str) -> Optional[str]:
        """
        Verify and consume a token. Returns user_id on success, None otherwise.
        The token is deleted after first use.
        """
        with self._lock:
            entry = self._tokens.get(token)
            if not entry:
                return None
            if datetime.now(timezone.utc) > entry["expires_at"]:
                del self._tokens[token]
                return None
            del self._tokens[token]
            return entry["user_id"]
