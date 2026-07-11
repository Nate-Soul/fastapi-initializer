import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import CHAR, TypeDecorator


class Base(DeclarativeBase):
    """Declarative base for all ORM models. Alembic reads ``Base.metadata``."""


class GUID(TypeDecorator):
    """Platform-independent UUID: native UUID on Postgres, CHAR(36) on SQLite (dev/test)."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return value if isinstance(value, uuid.UUID) else uuid.UUID(value)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_aware_utc(dt: datetime) -> datetime:
    """SQLite (used for local dev/tests) round-trips DateTime columns as naive, even
    though we always write UTC-aware values. Postgres preserves the offset natively.
    Normalize here so comparisons against datetime.now(timezone.utc) work identically
    on both backends instead of raising TypeError on SQLite only."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


class TimestampedBase(Base):
    """Abstract base: UUID PK (non-enumerable), created_at/updated_at, soft delete."""

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
