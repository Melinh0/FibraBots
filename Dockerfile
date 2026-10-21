FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    FIBRABOTS_HEADLESS=1

COPY --from=ghcr.io/astral-sh/uv:0.11.4 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev
RUN uv run --no-sync playwright install --with-deps chromium

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["fibrabots"]
CMD ["--help"]
