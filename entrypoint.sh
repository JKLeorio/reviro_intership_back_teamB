#!/usr/bin/env bash
set -e

echo "Creating tables..."
uv run alembic upgrade head

echo "Creating superuser if not exists..."

uv run manage.py createsuperuser --email "$SUPERUSER_EMAIL" --password "$SUPERUSER_PASSWORD"

uv run main.py
