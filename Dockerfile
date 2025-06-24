FROM ghcr.io/astral-sh/uv:0.7.14-python3.11-alpine@sha256:60f35c63895a66c84e3e71d0e71cf52ee1992feba6813d48e30c8ea84ffb0d80

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/server.py:mcp"]
