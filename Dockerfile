FROM ghcr.io/astral-sh/uv:0.7.16-python3.11-alpine@sha256:b498e56da929ad3487bc277bafedf36852105fdf5af99f564667e6a82c30009d

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/server.py:mcp"]
