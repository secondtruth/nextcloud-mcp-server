FROM ghcr.io/astral-sh/uv:0.8.13-python3.11-alpine@sha256:69442b1f3990c7f0262c06087f2ebf4c690a15c7fac08aeec6ad948c28783ca7

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/app.py:mcp"]
