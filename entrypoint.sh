#!/usr/bin/env bash
set -e

echo "Creating tables..."
uv run alembic upgrade head

uv run main.py
