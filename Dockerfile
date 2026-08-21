FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY bd ./bd
COPY docker-entrypoint.sh ./

RUN uv sync --frozen --extra dev
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
