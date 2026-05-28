"""Auth token generation & validation."""

from __future__ import annotations

import json
import time

from jose import exceptions, jwe

from app.core.config import settings


class AuthTokenGenerator:
    @staticmethod
    def generate_auth_token() -> str:
        payload = json.dumps(
            {"code": settings.system_code, "timestamp": int(time.time() * 1000)},
            separators=(",", ":"),
        )
        return jwe.encrypt(payload.encode(), settings.aes_key, algorithm="dir", encryption="A256GCM")

    @staticmethod
    def validate_token(token: str) -> dict | None:
        try:
            raw = jwe.decrypt(token, settings.aes_key)
            data = json.loads(raw)
            ts = data.get("timestamp", 0)
            if time.time() * 1000 - ts > 5 * 60 * 1000:
                return None
            return data
        except (exceptions.JWEError, ValueError, KeyError):
            return None
