FROM ghcr.io/astral-sh/uv:0.7.20-python3.11-alpine@sha256:5676209b5e686d60bfae32d9f656bf935a5613759860c447ed90a37a89192caa

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/server.py:mcp"]
