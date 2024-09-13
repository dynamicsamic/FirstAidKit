FROM python:3.12.3-slim-bookworm

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.3.4 /uv /bin/uv

COPY uv.lock pyproject.toml /app/

RUN uv sync --frozen
ENV PATH="/app/.venv/bin:$PATH"

COPY src/ /app/src
