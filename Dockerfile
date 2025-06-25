FROM ghcr.io/astral-sh/uv:0.7.15-python3.11-alpine@sha256:5f7673881c31d1c373972eb9c8e452122c2a136c0705e25cf967261473a57bc4

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/server.py:mcp"]
