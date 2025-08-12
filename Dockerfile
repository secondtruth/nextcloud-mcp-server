FROM ghcr.io/astral-sh/uv:0.8.9-python3.11-alpine@sha256:4beddf86f831ba10cb2bbc34ad917ed2395e1a22f0ef7aee9fb939f50e97bfa0

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/app.py:mcp"]
