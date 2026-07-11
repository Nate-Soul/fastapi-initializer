FROM python:3.11-slim

# Don't buffer stdout/stderr; no .pyc files in the image.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first (layer-cache friendly — only busts when requirements change).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source + migrations.
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

# Run as a non-root user.
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

# PORT is injected by most managed platforms (Render, Railway, Fly) at runtime.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
