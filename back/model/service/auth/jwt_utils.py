import os
import time
from functools import wraps
from typing import Optional, Dict, Any

import jwt
from flask import request, g

from model.service.errors import AuthError


def _get_secret() -> str:
    secret = os.getenv("JWT_SECRET", "replace_me")
    return secret


def _get_exp_minutes() -> int:
    try:
        return int(os.getenv("JWT_EXPIRES_MIN", "1440"))
    except ValueError:
        return 1440


def create_jwt(payload: Dict[str, Any], minutes: Optional[int] = None) -> str:
    exp_minutes = minutes if minutes is not None else _get_exp_minutes()
    payload = dict(payload)
    payload.update({
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_minutes * 60,
    })
    token = jwt.encode(payload, _get_secret(), algorithm="HS256")
    # PyJWT 2.x returns str
    return token


def decode_jwt(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, _get_secret(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired", status=401, code="TOKEN_EXPIRED")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token", status=401, code="TOKEN_INVALID")


def _extract_token() -> Optional[str]:
    # 1) Cookie first
    token = request.cookies.get("auth")
    if token:
        return token
    # 2) Authorization: Bearer <token>
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return None


def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        if not token:
            raise AuthError("Missing token", status=401, code="TOKEN_MISSING")
        claims = decode_jwt(token)  # will raise if invalid/expired
        g.user_claims = claims
        return fn(*args, **kwargs)
    return wrapper
