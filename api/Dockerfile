# # api/Dockerfile
# FROM python:3.11-slim AS base
#
# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1
#
# RUN pip install --no-cache-dir poetry
#
# WORKDIR /app
#
# COPY pyproject.toml ./
#
# RUN poetry config virtualenvs.create false \
#     && poetry install --no-root --no-interaction --no-ansi --only main
#
# FROM base AS development
#
# COPY app ./app
#
# EXPOSE 8000
#
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
#
# FROM base AS production
#
# COPY app ./app
#
# EXPOSE 8000
#
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# api/Dockerfile
FROM python:3.11-slim AS development
# Development stage
RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi --only main

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install development dependencies if you have them
# COPY requirements-dev.txt .
# RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Default development command with reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM python:3.11-slim AS production

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi --only main
    
# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Production command (no reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
