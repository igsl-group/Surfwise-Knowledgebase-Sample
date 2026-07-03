"""CRUD for API tokens (BookStack-style id:secret). Secrets are stored hashed and
returned only once at creation/rotation."""
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import ApiToken
from app.schemas import TokenCreate, TokenCreated, TokenRead, TokenUpdate
from app.security import hash_secret, require_token

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


async def _get(session: AsyncSession, tid: int) -> ApiToken:
    tok = (
        await session.execute(select(ApiToken).where(ApiToken.id == tid))
    ).scalar_one_or_none()
    if tok is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Token not found")
    return tok


@router.get("", response_model=list[TokenRead])
async def list_tokens(
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> list[ApiToken]:
    return list(
        (await session.execute(select(ApiToken).order_by(ApiToken.id))).scalars().all()
    )


@router.post("", response_model=TokenCreated, status_code=status.HTTP_201_CREATED)
async def create_token(
    payload: TokenCreate,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> TokenCreated:
    token_id = (payload.token_id or ("kb_" + secrets.token_hex(6))).strip()
    secret = payload.secret or secrets.token_urlsafe(24)
    dup = (
        await session.execute(select(ApiToken).where(ApiToken.token_id == token_id))
    ).scalar_one_or_none()
    if dup is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="token_id already exists")
    tok = ApiToken(name=payload.name, token_id=token_id, secret_hash=hash_secret(secret))
    session.add(tok)
    await session.commit()
    await session.refresh(tok)
    return TokenCreated(id=tok.id, name=tok.name, token_id=tok.token_id, secret=secret)


@router.put("/{tid}", response_model=TokenRead)
async def update_token(
    tid: int,
    payload: TokenUpdate,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> ApiToken:
    tok = await _get(session, tid)
    if payload.name is not None:
        tok.name = payload.name
    await session.commit()
    await session.refresh(tok)
    return tok


@router.post("/{tid}/rotate", response_model=TokenCreated)
async def rotate_token(
    tid: int,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> TokenCreated:
    tok = await _get(session, tid)
    secret = secrets.token_urlsafe(24)
    tok.secret_hash = hash_secret(secret)
    await session.commit()
    await session.refresh(tok)
    return TokenCreated(id=tok.id, name=tok.name, token_id=tok.token_id, secret=secret)


@router.delete("/{tid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_token(
    tid: int,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> None:
    count = (await session.execute(select(func.count(ApiToken.id)))).scalar_one()
    if count <= 1:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the last remaining token (would lock out API access).",
        )
    tok = await _get(session, tid)
    await session.delete(tok)
    await session.commit()
