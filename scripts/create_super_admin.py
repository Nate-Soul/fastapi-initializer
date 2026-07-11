"""Create (or promote) a super-admin user.

Usage:
    python -m scripts.create_super_admin --email admin@example.com --password 'S3cret!!'

Or via environment variables (useful in CI / container entrypoints):
    ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD='S3cret!!' python -m scripts.create_super_admin

Idempotent: if a user with the email already exists, it is promoted to ADMIN and
its password is left unchanged.
"""

import argparse
import asyncio
import os

from sqlalchemy import select

import app.infrastructure.database.registry  # noqa: F401  (configure all mappers)
from app.core.security import hash_password
from app.infrastructure.database.session import AsyncSessionLocal
from app.modules.users.models import Role, User


async def create_super_admin(email: str, password: str) -> None:
    async with AsyncSessionLocal() as session:
        existing = (
            await session.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()

        if existing is not None:
            if existing.role != Role.ADMIN:
                existing.role = Role.ADMIN
                await session.commit()
                print(f"Promoted existing user {email} to ADMIN.")
            else:
                print(f"User {email} is already an ADMIN. Nothing to do.")
            return

        admin = User(
            email=email,
            hashed_password=hash_password(password),
            first_name="Super",
            last_name="Admin",
            role=Role.ADMIN,
        )
        session.add(admin)
        await session.commit()
        print(f"Created super-admin {email}.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or promote a super-admin user.")
    parser.add_argument("--email", default=os.getenv("ADMIN_EMAIL"))
    parser.add_argument("--password", default=os.getenv("ADMIN_PASSWORD"))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if not args.email or not args.password:
        raise SystemExit(
            "email and password are required (pass --email/--password or set "
            "ADMIN_EMAIL/ADMIN_PASSWORD)."
        )
    asyncio.run(create_super_admin(args.email, args.password))


if __name__ == "__main__":
    main()
