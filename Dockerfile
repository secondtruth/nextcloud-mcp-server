FROM ghcr.io/astral-sh/uv:0.8.7-python3.11-alpine@sha256:1c2a92cd2c18182c071e6c434138ffb2f7c5c598809918484405899aab166de1

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/app.py:mcp"]
