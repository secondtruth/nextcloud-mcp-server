FROM ghcr.io/astral-sh/uv:0.8.15-python3.11-alpine@sha256:e471ce4bfa92cc0fde030ed04f96c12aec41a7291451cd941b35b482200ed3a4

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/app.py:mcp"]
