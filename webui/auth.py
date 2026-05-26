"""WebUI Authentication - Cookie-based session auth using stdlib only."""

import os
import hashlib
import hmac
import secrets
import time
import json
import base64
from typing import Optional

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import RedirectResponse

# Session config
SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "stock-skills-secret-change-in-prod-2024")
SESSION_MAX_AGE = int(os.environ.get("AUTH_SESSION_HOURS", "24")) * 3600
COOKIE_NAME = "ss_session"

# Credentials from env (default: admin / admin123)
AUTH_USERNAME = os.environ.get("AUTH_USERNAME", "admin")
# Store as PBKDF2-HMAC-SHA256 hex digest
# Default is hash of "admin123"
_DEFAULT_HASH = hashlib.pbkdf2_hmac(
    "sha256", b"admin123", b"stock-skills-salt", 200_000
).hex()
AUTH_PASSWORD_HASH = os.environ.get("AUTH_PASSWORD_HASH", _DEFAULT_HASH)
AUTH_PASSWORD_SALT = os.environ.get("AUTH_PASSWORD_SALT", "stock-skills-salt")

# Auth enabled flag
AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "true").lower() not in ("false", "0", "off")


def hash_password(plain: str, salt: str = "stock-skills-salt") -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", plain.encode(), salt.encode(), 200_000
    ).hex()


def verify_password(plain: str, stored_hash: str) -> bool:
    candidate = hash_password(plain, AUTH_PASSWORD_SALT)
    return hmac.compare_digest(candidate, stored_hash)


def _sign(payload: str) -> str:
    sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return sig


def create_session_token(username: str) -> str:
    data = json.dumps({"user": username, "exp": int(time.time()) + SESSION_MAX_AGE})
    encoded = base64.urlsafe_b64encode(data.encode()).decode()
    sig = _sign(encoded)
    return f"{encoded}.{sig}"


def decode_session_token(token: str) -> Optional[str]:
    try:
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            return None
        encoded, sig = parts
        expected = _sign(encoded)
        if not hmac.compare_digest(sig, expected):
            return None
        data = json.loads(base64.urlsafe_b64decode(encoded.encode()).decode())
        if data.get("exp", 0) < int(time.time()):
            return None
        return data.get("user")
    except Exception:
        return None


def get_current_user(request: Request) -> Optional[str]:
    if not AUTH_ENABLED:
        return "guest"
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return decode_session_token(token)


def require_auth(request: Request) -> str:
    """FastAPI dependency: redirect to login if not authenticated."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": f"/login?next={request.url.path}"},
        )
    return user


def set_session_cookie(response: Response, username: str) -> None:
    token = create_session_token(username)
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME)
