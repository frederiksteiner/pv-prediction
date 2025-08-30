# =========================
# Base Python image
# =========================
FROM python:3.12-slim as python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=2.1.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# =========================
# Builder
# =========================
FROM python-base as builder
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
       curl build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR $PYSETUP_PATH

# Copy only dependency files first for better caching
COPY poetry.lock pyproject.toml ./

# Install dependencies (no dev)
RUN poetry install --without=dev --no-root

# =========================
# Development image
# =========================
FROM python-base as development
ENV FASTAPI_ENV=development
WORKDIR $PYSETUP_PATH

# Copy venv + poetry from builder
COPY --from=builder $POETRY_HOME $POETRY_HOME
COPY --from=builder $PYSETUP_PATH $PYSETUP_PATH

# Install dev dependencies too
RUN poetry install --with=dev --no-root

WORKDIR /app
EXPOSE 8000
CMD ["uvicorn", "--reload", "pv_prediction.main:app", "--host", "0.0.0.0", "--port", "8000"]

# =========================
# Production image
# =========================
FROM python-base as production
ENV FASTAPI_ENV=production

# Copy dependencies from builder
COPY --from=builder $PYSETUP_PATH $PYSETUP_PATH

# Copy application code
WORKDIR /app
COPY ./src/pv_prediction /app/pv_prediction

# Use gunicorn with uvicorn workers
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "pv_prediction.main:app", "--bind", "0.0.0.0:8000"]
