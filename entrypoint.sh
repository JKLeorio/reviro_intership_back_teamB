#!/usr/bin/env bash
set -e

echo 'Setting up alembic directories...'
mkdir -p alembic/versions

echo 'Setting up fresh database schema...'
uv run alembic stamp base

echo "Generating migrations from current database..."
uv run alembic revision --autogenerate -m 'deployment schema'

echo "Creating tables..."
uv run alembic upgrade head

uv run main.py
