FROM ghcr.io/astral-sh/uv:0.8.8-python3.11-alpine@sha256:f50a228be4e0f4b3676b10d63d63ece6cf8bc768c3eeadd3fe1a78c25f692600

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/app.py:mcp"]
