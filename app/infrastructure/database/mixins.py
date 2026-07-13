"""Composable ORM mixins.

Each mixin contributes one concern (identity, timestamps, soft delete) and nothing
else, so a model can pick exactly the columns it needs:

    class Widget(UUIDPrimaryKeyMixin, TimestampMixin, Base):   # no soft delete
        __tablename__ = "widgets"

``TimestampedBase`` bundles all three for the common case. Mixins are plain classes
(not ``DeclarativeBase`` subclasses) — SQLAlchemy 2.0 resolves their ``mapped_column``
annotations when they appear in a model's MRO alongside a declarative ``Base``.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import GUID, Base, utcnow


class UUIDPrimaryKeyMixin:
    """Non-enumerable UUID primary key (safe to expose in URLs, unlike serial ints)."""

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    """``created_at`` / ``updated_at``, both stored as UTC-aware timestamps."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class SoftDeleteMixin:
    """``deleted_at`` marker for soft deletes. Rows are hidden by filtering on it
    rather than physically removed, so history is recoverable."""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class TimestampedBase(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Batteries-included base: UUID PK + created_at/updated_at + soft delete.

    Use this for most models; drop down to the individual mixins when a model needs
    a different combination.
    """

    __abstract__ = True
