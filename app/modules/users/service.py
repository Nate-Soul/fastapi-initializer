import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.users.models import User


async def list_users(db: AsyncSession, limit: int, offset: int) -> tuple[list[User], int]:
    """Return a page of non-deleted users plus the total count."""
    base = select(User).where(User.deleted_at.is_(None))
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        (await db.execute(base.order_by(User.created_at.desc()).limit(limit).offset(offset)))
        .scalars()
        .all()
    )
    return list(rows), total


async def get_user_or_404(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = (
        await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    ).scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")
    return user


async def update_user(
    db: AsyncSession, user: User, first_name: str | None, last_name: str | None
) -> User:
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    await db.commit()
    await db.refresh(user)
    return user


async def soft_delete_user(db: AsyncSession, user: User) -> None:
    user.deleted_at = datetime.now(timezone.utc)  # soft delete, not a hard DELETE
    await db.commit()
