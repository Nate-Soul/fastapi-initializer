import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# bcrypt, cost factor 12 (passlib default for bcrypt is 12 rounds — explicit here so it's
# never silently lowered by a passlib/library upgrade).
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "role": role, "type": "access", "iat": now, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Raises jose.JWTError on invalid/expired/tampered token. Algorithm pinned explicitly
    (never trusts an alg claimed in the token header, which prevents alg-confusion attacks)."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def new_raw_refresh_token() -> str:
    """Cryptographically random opaque token — not a JWT. We only ever store its hash."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw_token: str) -> str:
    # SHA-256 is sufficient here: the input is already a 48-byte random token, not a
    # low-entropy password, so we don't need bcrypt's slow, salted KDF for this value.
    return hashlib.sha256(raw_token.encode()).hexdigest()


def refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_token",
    "new_raw_refresh_token",
    "hash_refresh_token",
    "refresh_token_expiry",
    "JWTError",
]
