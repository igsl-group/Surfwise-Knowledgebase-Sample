import hashlib
import hmac

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.models import ApiToken


def hash_secret(secret: str) -> str:
    """Hash a token secret for at-rest storage (SHA-256 of a high-entropy token)."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


async def require_token(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> ApiToken:
    """Validate ``Authorization: Token <id>:<secret>`` (any valid token = read access)."""
    if not authorization or not authorization.startswith("Token "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Expected 'Token <id>:<secret>'.",
        )
    raw = authorization[len("Token ") :].strip()
    if ":" not in raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token. Expected 'Token <id>:<secret>'.",
        )
    token_id, _, secret = raw.partition(":")
    token = (
        await session.execute(select(ApiToken).where(ApiToken.token_id == token_id))
    ).scalar_one_or_none()
    # constant-time comparison; still compute a hash when token is missing to reduce timing signal
    expected = token.secret_hash if token is not None else hash_secret("")
    if not hmac.compare_digest(expected, hash_secret(secret)) or token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token."
        )
    return token


async def require_admin_token(
    token: ApiToken = Depends(require_token),
) -> ApiToken:
    """Require an admin-scoped token (write/management operations)."""
    if not token.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires an admin API token. Read-only tokens cannot modify data.",
        )
    return token


_ui_basic = HTTPBasic(auto_error=True)


def require_ui_auth(credentials: HTTPBasicCredentials = Depends(_ui_basic)) -> str:
    """HTTP Basic gate for the admin web UI (username/password from KB_UI_* env)."""
    settings = get_settings()
    ok_user = hmac.compare_digest(credentials.username, settings.ui_username)
    ok_pass = hmac.compare_digest(credentials.password, settings.ui_password)
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid UI credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
