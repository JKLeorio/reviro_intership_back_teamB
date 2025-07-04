#!/usr/bin/env bash

alembic revision --autogenerate -m "project migrations"

uv run alembic upgrade head

uv run main.py