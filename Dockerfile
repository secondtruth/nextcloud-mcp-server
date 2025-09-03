FROM ghcr.io/astral-sh/uv:0.8.15-python3.11-alpine@sha256:22e07305bb47a2802145d8e495f403009d8e2843ce9ffcb818b45256224776ae

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/app.py:mcp"]
