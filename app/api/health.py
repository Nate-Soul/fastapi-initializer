from fastapi import APIRouter
from sqlalchemy import text

from app.common.deps import DbSession

router = APIRouter(tags=["health"])


@router.get("/health")
async def liveness():
    """Liveness probe — process is up. No dependencies touched."""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness(db: DbSession):
    """Readiness probe — verifies the database is reachable before taking traffic."""
    await db.execute(text("SELECT 1"))
    return {"status": "ready"}
