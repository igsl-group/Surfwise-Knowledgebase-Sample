import hashlib

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import ApiToken


def hash_secret(secret: str) -> str:
    """Hash a token secret for at-rest storage (SHA-256)."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


async def require_token(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> ApiToken:
    """Validate a BookStack-style ``Authorization: Token <id>:<secret>`` header."""
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
    result = await session.execute(select(ApiToken).where(ApiToken.token_id == token_id))
    token = result.scalar_one_or_none()
    if token is None or token.secret_hash != hash_secret(secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token."
        )
    return token
