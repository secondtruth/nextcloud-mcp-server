FROM ghcr.io/astral-sh/uv:0.8.0-python3.11-alpine@sha256:36066e5a0981b0718132a0872592cfe2c887a72332491e8479624dcc7922fdc7

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/server.py:mcp"]
