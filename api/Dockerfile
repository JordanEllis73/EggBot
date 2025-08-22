# api/Dockerfile
FROM python:3.12.11-slim-bookworm AS base

# Install system dependencies first (better caching)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    bluetooth \
    bluez \
    libbluetooth-dev \
    libglib2.0-dev \
    pkg-config \
    python3-dev \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first to avoid version parsing issues
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Set environment variables for compilation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

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

# Install bluepy3 separately with pip to ensure it compiles correctly
RUN pip install --no-cache-dir bluepy3==0.4.1

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

# Install bluepy3 separately with pip to ensure it compiles correctly
RUN pip install --no-cache-dir bluepy3==0.4.1

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Production command (no reload, more workers)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
