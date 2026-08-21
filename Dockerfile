FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY bd ./bd

RUN uv sync --frozen --extra dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "portal.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app/src"]
