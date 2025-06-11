# -----------------------------
# Base Images
# -----------------------------
# UV used as builder image to minimize final image size while maintaining modern package management
FROM ghcr.io/astral-sh/uv:0.4.20 AS uv

# Slim variant reduces base size by ~700MB while keeping Python functionality
FROM python:3.13-slim

# -----------------------------
# Environment Configuration
# -----------------------------
# Critical for container logging - prevents output buffering that could delay error detection
ENV PYTHONUNBUFFERED=1

ENV UV_LINK_MODE=copy \
  UV_COMPILE_BYTECODE=1 \
  UV_PYTHON_DOWNLOADS=never \
  UV_PROJECT_ENVIRONMENT=/.venv \
  UV_LOCKED=1
# critical to make sure its using uv.lock

# -----------------------------
# System Dependencies
# -----------------------------
# Single RUN command with cleanup reduces image size by combining layers and removing package caches
RUN apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  # Runtime operation and debug tools
  curl \
  psmisc \
  tree \
  \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && rm -rf /var/cache/apt/*

# -----------------------------
# Application Setup
# -----------------------------
# Multi-stage build keeps only the UV binary, discarding build context
COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app

# -----------------------------
# Dependencies Installation
# -----------------------------
# Split dependency installation improves rebuild speed by caching base dependencies
COPY pyproject.toml uv.lock ./
RUN touch README.md
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked --no-install-project 

# Application code changes won't invalidate dependency cache
COPY . /app
# RUN --mount=type=cache,target=/root/.cache/uv \
#   uv sync --locked --no-install-project

# -----------------------------
# Runtime Configuration
# -----------------------------
ENV PATH="$UV_PROJECT_ENVIRONMENT/bin:$PATH"

EXPOSE 8000

# -----------------------------
# Health Check
# -----------------------------
# Allows orchestrators to monitor application health and manage container lifecycle
HEALTHCHECK \
  --start-period=10s \
  --interval=30s \
  --timeout=10s \
  --retries=3 \
  CMD curl -f  http://localhost:8000/docs

# -----------------------------
# Launch Command
# -----------------------------
# Can be overwritten by e.g. api-tests. We use the sane default of starting the web server
ENTRYPOINT ["sh", "./entrypoint.sh"]