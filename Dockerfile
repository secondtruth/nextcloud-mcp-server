FROM ghcr.io/astral-sh/uv:0.8.3-python3.11-alpine@sha256:886c19178558b951bbb9cb242deb94e7e37f9cba5d0dc018cd210ccd6b5116db

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/app.py:mcp"]
