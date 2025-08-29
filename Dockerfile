FROM ghcr.io/astral-sh/uv:0.8.14-python3.11-alpine@sha256:7b1463148981d57ed2d9c2950f570fe5fdd88570970f9f56f6e0e5a8829eca95

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/app.py:mcp"]
