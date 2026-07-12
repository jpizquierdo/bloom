# Minimal single-instance image for Bloom (uv-based).
# Migrations + admin bootstrap run on startup (FastAPI lifespan), so the
# container just needs to start the API.
FROM python:3.13-slim

# Bring in uv from its official image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

# 1) Install dependencies first (cached unless pyproject/lock change).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# 2) Copy the app and install the project itself.
COPY . .
RUN uv sync --frozen --no-dev

# Run using the project's virtualenv.
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["fastapi", "run", "bloom/main.py", "--host", "0.0.0.0", "--port", "8000"]
