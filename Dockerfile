FROM ghcr.io/astral-sh/uv:0.8.5-python3.11-alpine@sha256:6482e26beeca9057f1ae4bcc4f1a5cc0c0ed7d7eb0f267676ef6a49028f16f9d

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/app.py:mcp"]
