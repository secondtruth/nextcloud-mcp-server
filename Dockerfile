FROM ghcr.io/astral-sh/uv:0.8.16-python3.11-alpine@sha256:6f2ebcb9ed454dbfd0f324dff39807d0edaac19560839667b0b52e37996212a1

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/app.py:mcp"]
