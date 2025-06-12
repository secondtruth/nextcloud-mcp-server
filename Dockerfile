FROM ghcr.io/astral-sh/uv:0.7.13-python3.11-alpine@sha256:49e33cfbb4b3a08293fc539829adf9f5790f95bb123bf327acdb5909f0531043

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/server.py:mcp"]
