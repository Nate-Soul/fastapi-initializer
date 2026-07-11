"""Unit tests for the auth service layer — exercised directly against a session,
no HTTP layer involved."""

import pytest

from app.core.exceptions import ConflictError, UnauthorizedError
from app.modules.auth import service


async def test_register_then_authenticate_roundtrip(db_session):
    async with db_session() as session:
        user = await service.register_user(
            session, email="svc@example.com", password="supersecret1", first_name="Svc", last_name="Tester"
        )
        assert user.id is not None
        assert user.hashed_password != "supersecret1"  # never stored in plaintext

        authed = await service.authenticate(session, email="svc@example.com", password="supersecret1")
        assert authed.id == user.id


async def test_authenticate_wrong_password_raises(db_session):
    async with db_session() as session:
        await service.register_user(
            session, email="svc2@example.com", password="supersecret1", first_name="A", last_name="B"
        )
        with pytest.raises(UnauthorizedError):
            await service.authenticate(session, email="svc2@example.com", password="nope")


async def test_register_duplicate_email_raises_conflict(db_session):
    async with db_session() as session:
        await service.register_user(
            session, email="dup@example.com", password="supersecret1", first_name="A", last_name="B"
        )
        with pytest.raises(ConflictError):
            await service.register_user(
                session, email="dup@example.com", password="supersecret1", first_name="C", last_name="D"
            )
