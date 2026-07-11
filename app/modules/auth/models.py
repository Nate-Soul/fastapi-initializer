import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import GUID, TimestampedBase


class RefreshToken(TimestampedBase):
    """
    We never store the raw refresh token — only a hash of it, same principle as
    passwords. On refresh, the presented token's hash is looked up; if found,
    unrevoked, and unexpired, it is revoked (rotation) and a new pair is issued.
    Reuse of an already-revoked token indicates theft and invalidates the whole
    token family (all of the user's refresh tokens).
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")
