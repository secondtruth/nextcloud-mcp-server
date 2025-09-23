FROM ghcr.io/astral-sh/uv:0.8.20-python3.11-alpine@sha256:8c24c223d63cb6b997101852cb7bc767b349918652e05e3cba20c93c899cb3d5

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

ENTRYPOINT ["/app/.venv/bin/nextcloud-mcp-server", "--host", "0.0.0.0"]
