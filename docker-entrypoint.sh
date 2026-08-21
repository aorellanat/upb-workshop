#!/bin/sh
set -e

uv run inicializar-bd

exec uv run uvicorn portal.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/src
