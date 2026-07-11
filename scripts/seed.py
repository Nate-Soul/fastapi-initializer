"""Seed the database with demo data for local development.

Usage:
    python -m scripts.seed

Creates one admin and one regular user (idempotent — skips users that already exist).
Passwords are printed so you can log in immediately. Never run this against production.
"""

import asyncio

from sqlalchemy import select

import app.infrastructure.database.registry  # noqa: F401  (configure all mappers)
from app.core.security import hash_password
from app.infrastructure.database.session import AsyncSessionLocal
from app.modules.users.models import Role, User

_DEMO_USERS = [
    {"email": "admin@example.com", "password": "adminpass1", "first_name": "Ada", "last_name": "Admin", "role": Role.ADMIN},
    {"email": "user@example.com", "password": "userpass1", "first_name": "Uma", "last_name": "User", "role": Role.USER},
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        for spec in _DEMO_USERS:
            exists = (
                await session.execute(select(User).where(User.email == spec["email"]))
            ).scalar_one_or_none()
            if exists is not None:
                print(f"skip  {spec['email']} (already exists)")
                continue
            session.add(
                User(
                    email=spec["email"],
                    hashed_password=hash_password(spec["password"]),
                    first_name=spec["first_name"],
                    last_name=spec["last_name"],
                    role=spec["role"],
                )
            )
            print(f"seed  {spec['email']} / {spec['password']}  ({spec['role'].value})")
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
