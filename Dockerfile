FROM ghcr.io/astral-sh/uv:0.8.6-python3.11-alpine@sha256:15e7f7ee738f1b8a0e1ed95da7cf821c58b77d3d15275bf8f4605fbbf36679f4

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/app.py:mcp"]
