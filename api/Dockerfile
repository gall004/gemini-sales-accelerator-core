# =============================================================================
# Gemini Sales Accelerator Core — API Development Dockerfile
#
# Optimized for local development with hot-reload via uvicorn --reload.
# Production Dockerfile will strip dev dependencies and use gunicorn + uvicorn.
# =============================================================================

FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required by asyncpg and psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Source code is mounted as a volume in docker-compose.yml (not COPY'd)
# This enables hot-reload without rebuilding the container.

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
