FROM ghcr.io/astral-sh/uv:0.8.4-python3.11-alpine@sha256:f2c5b953b713f455bcac4429303bb21d7d2547d56a64e1a7b2517cc9f0563f0f

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/server.py:mcp"]
