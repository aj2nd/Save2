# Base Image
FROM python:3.11-slim

# Metadata
LABEL maintainer="anandhu723"
LABEL version="1.0.0"
LABEL created="2025-06-08 18:23:38"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.5.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${POETRY_HOME}/bin:$PATH"

# Copy project files
COPY poetry.lock pyproject.toml ./
COPY saveai ./saveai

# Install dependencies
RUN poetry install --no-dev --no-root

# Copy configuration files
COPY config/*.yml ./config/
COPY alembic.ini ./

# Create non-root user
RUN useradd -m -s /bin/bash appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Start application
CMD ["poetry", "run", "uvicorn", "saveai.main:app", "--host", "0.0.0.0", "--port", "8000"]
