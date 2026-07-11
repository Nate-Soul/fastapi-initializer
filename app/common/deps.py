from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db

DbSession = Annotated[AsyncSession, Depends(get_db)]
