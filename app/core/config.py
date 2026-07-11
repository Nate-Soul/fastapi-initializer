from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "FastAPI Boilerplate"
    environment: str = "development"
    debug: bool = True

    # Swappable via env var alone: sqlite+aiosqlite:///./dev.db for local dev/tests,
    # postgresql+asyncpg://... in production. No code change required to switch.
    database_url: str = "sqlite+aiosqlite:///./dev.db"

    secret_key: str = "dev-only-insecure-key-override-in-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    cors_origins: list[str] = ["http://localhost:3000"]

    rate_limit_default: str = "100/minute"
    rate_limit_auth: str = "5/minute"

    # Logging (see app/core/logging.py). log_json=True emits one JSON object per
    # line — turn it on in production for log aggregators; keep it off in dev.
    log_level: str = "INFO"
    log_json: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
