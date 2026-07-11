from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_raw_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.infrastructure.database.base import as_aware_utc
from app.modules.auth.models import RefreshToken
from app.modules.users.models import User


async def register_user(
    db: AsyncSession, email: str, password: str, first_name: str, last_name: str
) -> User:
    existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("An account with this email already exists")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        first_name=first_name,
        last_name=last_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = (
        await db.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
    ).scalar_one_or_none()

    # Same error for "no such user" and "wrong password" — don't leak which one it was.
    if user is None or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Incorrect email or password")
    if not user.is_active:
        raise UnauthorizedError("Account is disabled")
    return user


async def issue_tokens(db: AsyncSession, user: User) -> tuple[str, str]:
    """Create an access token and persist a new refresh-token record.

    Returns ``(access_token, raw_refresh_token)``. The raw refresh token is only
    ever returned here (to be set as an httpOnly cookie by the caller); the DB
    stores its hash only.
    """
    access_token = create_access_token(subject=str(user.id), role=user.role.value)

    raw_refresh = new_raw_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=refresh_token_expiry(),
        )
    )
    await db.commit()
    return access_token, raw_refresh


async def rotate_refresh(db: AsyncSession, raw_token: str) -> User:
    """Validate and rotate a refresh token, returning the owning user.

    Revokes the presented token on success. Reuse of an already-revoked token
    revokes the whole family for that user (theft response).
    """
    token_hash = hash_refresh_token(raw_token)
    stored = (
        await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    ).scalar_one_or_none()

    if stored is None:
        raise UnauthorizedError("Invalid refresh token")

    if stored.revoked:
        # Reuse of a revoked token = likely theft. Nuke the whole family for this user.
        await db.execute(
            update(RefreshToken).where(RefreshToken.user_id == stored.user_id).values(revoked=True)
        )
        await db.commit()
        raise UnauthorizedError("Refresh token reuse detected; all sessions revoked")

    if as_aware_utc(stored.expires_at) < datetime.now(timezone.utc):
        raise UnauthorizedError("Refresh token expired")

    # Rotation: revoke the used token before issuing a new one.
    stored.revoked = True
    await db.commit()

    user = (
        await db.execute(select(User).where(User.id == stored.user_id))
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user


async def revoke_refresh(db: AsyncSession, raw_token: str) -> None:
    token_hash = hash_refresh_token(raw_token)
    await db.execute(
        update(RefreshToken).where(RefreshToken.token_hash == token_hash).values(revoked=True)
    )
    await db.commit()
