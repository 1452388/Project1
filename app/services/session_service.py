# -*- coding: utf-8 -*-
"""登录会话签发与校验。"""

import base64
import hashlib
import hmac
import json
import time

from app.config import settings


class SessionService:
    """基于签名 cookie 的轻量会话服务。"""

    cookie_name = "session"
    max_age = 60 * 60 * 24 * 7

    @classmethod
    def create(cls, user_id: int, role: str, guest_code: str | None = None) -> str:
        payload = {
            "user_id": user_id,
            "role": role,
            "guest_code": guest_code,
            "expires": int(time.time()) + cls.max_age,
        }
        encoded = cls._encode(payload)
        signature = hmac.new(
            settings.SECRET_KEY.encode(), encoded.encode(), hashlib.sha256
        ).hexdigest()
        return f"{encoded}.{signature}"

    @classmethod
    def decode(cls, token: str | None) -> dict | None:
        if not token or "." not in token:
            return None
        encoded, signature = token.rsplit(".", 1)
        expected = hmac.new(
            settings.SECRET_KEY.encode(), encoded.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        try:
            payload = json.loads(base64.urlsafe_b64decode(encoded).decode())
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        if payload.get("expires", 0) < time.time():
            return None
        return payload

    @staticmethod
    def _encode(payload: dict) -> str:
        return base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":")).encode()
        ).decode()