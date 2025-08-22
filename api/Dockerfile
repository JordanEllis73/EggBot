# api/Dockerfile
FROM python:3.12.11-slim-bookworm AS base

# Install system dependencies first (better caching)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    bluetooth \
    bluez \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first to avoid version parsing issues
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Poetry using pip with specific version
RUN pip install --no-cache-dir poetry==1.8.3

# Configure Poetry
RUN poetry config virtualenvs.create false

WORKDIR /app

# Development stage
FROM base AS development

# Copy Poetry files (both are important!)
COPY pyproject.toml poetry.lock* ./

# Install dependencies including dev dependencies
RUN poetry install --no-root --no-interaction --no-ansi --verbose

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Development command with reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base AS production

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Install only production dependencies
RUN poetry install --no-root --no-interaction --no-ansi --only main --verbose

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Production command (no reload, more workers)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
