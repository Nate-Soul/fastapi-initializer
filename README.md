# FastAPI Initializer

A lean, **production-grade FastAPI starter** — modular-monolith architecture, async
SQLAlchemy 2.0, JWT auth with rotating refresh tokens, RBAC, rate limiting, security
headers, structured logging, Alembic migrations, a consistent error envelope, Docker + CI,
and a real pytest suite.

Use it as a template to kickstart a new backend without wiring the boring-but-critical
parts from scratch.

## Stack

- **Framework**: FastAPI, versioned under `/api/v1`
- **DB**: async SQLAlchemy 2.0. Swap Postgres ↔ SQLite with one env var (`DATABASE_URL`), no
  code changes. Production: `postgresql+asyncpg://...`. Local/dev/test (no server needed):
  `sqlite+aiosqlite:///./dev.db`.
- **Migrations**: Alembic, async-aware `env.py`
- **Auth**: bcrypt password hashing (cost 12, explicit), JWT access tokens (algorithm pinned),
  opaque rotating refresh tokens in httpOnly cookies, hashed at rest; reuse of a rotated token
  revokes the whole token family.
- **RBAC**: `Role.ADMIN` / `Role.USER` enforced via `require_role(...)` / ownership checks —
  not just declared.
- **Rate limiting**: slowapi, tighter limit on `/auth/*` than the rest of the API.
- **Security headers**: HSTS (prod), CSP, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy, Permissions-Policy on every response.
- **Observability**: structlog structured logging + `X-Request-ID` correlation on every request.
- **Errors**: every error returns `{"error": {"code", "message", "details"}}`, including
  uncaught exceptions (never leaks a traceback to the client).
- **IDs**: UUID primary keys (non-enumerable), soft delete via `deleted_at`.
- **Health**: `/health` (liveness) and `/health/ready` (readiness — pings the DB).
- **Tests**: pytest + httpx `ASGITransport`, in-memory SQLite, unit + integration split.

## Architecture

Modular monolith. Cross-cutting infrastructure is separated from business modules; each
module owns its models/schemas/service/routes.

```
app/
├── main.py                 # app wiring: middleware, exception handlers, lifespan, routers
├── api/
│   ├── health.py           # /health + /health/ready
│   └── v1/router.py        # central v1 aggregator — includes each module's router
├── core/                   # config, security (hashing/JWT), exceptions, logging, events (lifespan)
├── common/                 # shared schemas (error envelope, Page) + deps (DbSession)
├── infrastructure/
│   ├── database/           # base (Base + GUID), mixins (Timestamp/SoftDelete/UUID PK), engine/session
│   └── middleware/         # security_headers, request_id, rate_limit, cors, error_handler
└── modules/
    ├── users/              # models, schemas, service, routes
    └── auth/               # models, schemas, service, routes, dependencies
```

Routes are thin — they parse the request, call a `service.py` function (which holds all
DB/business logic and takes an `AsyncSession` explicitly), and shape the response.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt                  # runtime + test/lint deps
cp .env.example .env                                 # edit SECRET_KEY at minimum
alembic upgrade head                                 # creates dev.db (sqlite) by default
uvicorn app.main:app --reload
```

Docs at `http://localhost:8000/docs` (disabled automatically when `ENVIRONMENT=production`).
Seed demo users: `python -m scripts.seed`.
Create an admin: `python -m scripts.create_super_admin --email you@example.com --password '...'`.

## With Docker

```bash
docker compose up --build      # API on :8000, Postgres on :5432, migrations auto-applied
```

## Switching to Postgres (without Docker)

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/appdb
```

Then `alembic upgrade head`. No application code changes.

## Testing & quality

```bash
pytest                                  # unit + integration
ruff check .
mypy app --ignore-missing-imports
```

CI (`.github/workflows/ci.yml`) runs ruff, mypy, migrations, pytest (70% coverage gate), and
a Docker build against a real Postgres service on every push/PR.

## Adding a new module

1. Create `app/modules/<name>/` with `models.py`, `schemas.py`, `service.py`, `routes.py`
   (and `dependencies.py` if it has its own auth needs).
2. Models extend `TimestampedBase` (UUID PK + timestamps + soft delete for free) from
   `app.infrastructure.database.mixins` — or compose the individual `UUIDPrimaryKeyMixin`,
   `TimestampMixin`, and `SoftDeleteMixin` when a model needs a different combination.
3. Register the module's `router` in `app/api/v1/router.py`.
4. Import the module's models in `alembic/env.py` so autogenerate sees them.
5. `alembic revision --autogenerate -m "add <name>"` — **check the generated file**:
   Alembic's autogenerate does not import the custom `GUID` type used for UUID columns; if
   the diff includes a UUID column, add `import app.infrastructure.database.base` to the
   migration by hand, or `alembic upgrade` raises `NameError`.

## Extension points (intentionally not shipped)

Kept lean on purpose. When a project needs them, add under `app/infrastructure/`:

- **Redis cache** — `infrastructure/cache/`
- **Email** (verification / password reset) — `infrastructure/email/` + a provider
- **OAuth / social login** — `infrastructure/oauth/`
- **External HTTP clients + circuit breaker** — `infrastructure/http_client/`
- **Background workers** (Celery / APScheduler) — `infrastructure/tasks/`

## Known ecosystem gotcha

`passlib` (1.7.4, unmaintained since 2020) breaks on `bcrypt>=4.1` — you'll get
`AttributeError: module 'bcrypt' has no attribute '__about__'`. `requirements.txt` pins
`bcrypt<4.1` for this reason; don't upgrade it without switching off passlib entirely.
