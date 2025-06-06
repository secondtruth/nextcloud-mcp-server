FROM ghcr.io/astral-sh/uv:0.7.12-python3.11-alpine@sha256:6ae30fad80c582f1ccfabd6d252fc5463a42816034e18049569ce28229c4c254

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/server.py:mcp"]
