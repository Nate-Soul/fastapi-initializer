import uuid

from fastapi import APIRouter, Query

from app.common.deps import DbSession
from app.common.schemas import Page
from app.core.exceptions import ForbiddenError
from app.modules.auth.dependencies import CurrentUser
from app.modules.users import service
from app.modules.users.models import Role
from app.modules.users.schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=Page[UserResponse])
async def list_users(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    # Only admins may list all users; listing other users' data is a privilege, not a default.
    if current_user.role != Role.ADMIN:
        raise ForbiddenError("Only admins can list users")

    items, total = await service.list_users(db, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    if current_user.role != Role.ADMIN and current_user.id != user_id:
        raise ForbiddenError("You may only view your own profile")
    return await service.get_user_or_404(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: uuid.UUID, body: UserUpdate, db: DbSession, current_user: CurrentUser):
    if current_user.role != Role.ADMIN and current_user.id != user_id:
        raise ForbiddenError("You may only edit your own profile")

    user = await service.get_user_or_404(db, user_id)
    return await service.update_user(db, user, body.first_name, body.last_name)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    if current_user.role != Role.ADMIN and current_user.id != user_id:
        raise ForbiddenError("You may only delete your own account")

    user = await service.get_user_or_404(db, user_id)
    await service.soft_delete_user(db, user)
