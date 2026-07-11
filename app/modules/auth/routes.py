from fastapi import APIRouter, Request, Response

from app.common.deps import DbSession
from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.infrastructure.middleware.rate_limit import limiter
from app.modules.auth import service
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.modules.users.models import User
from app.modules.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        path="/api/v1/auth",
    )


async def _issue_and_set_cookie(db: DbSession, user: User, response: Response) -> TokenResponse:
    access_token, raw_refresh = await service.issue_tokens(db, user)
    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=access_token)


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit(settings.rate_limit_auth)
async def register(request: Request, body: RegisterRequest, db: DbSession):
    return await service.register_user(
        db,
        email=body.email,
        password=body.password,
        first_name=body.first_name,
        last_name=body.last_name,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_auth)
async def login(request: Request, body: LoginRequest, db: DbSession, response: Response):
    user = await service.authenticate(db, email=body.email, password=body.password)
    return await _issue_and_set_cookie(db, user, response)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_auth)
async def refresh(request: Request, db: DbSession, response: Response):
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        raise UnauthorizedError("Missing refresh token")

    user = await service.rotate_refresh(db, raw_token)
    return await _issue_and_set_cookie(db, user, response)


@router.post("/logout", status_code=204)
async def logout(request: Request, db: DbSession, response: Response):
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token:
        await service.revoke_refresh(db, raw_token)
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/v1/auth")
