#!/usr/bin/env bash

uv run alembic revision --autogenerate -m "project migrations"

uv run alembic upgrade head

uv run main.py