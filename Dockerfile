FROM ghcr.io/astral-sh/uv:0.8.17-python3.11-alpine@sha256:2a2cae80b7d3b3b3c7f94ec3ed91e9b3ca2524a7a429824fbbadd9954fa5d6b6

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

ENTRYPOINT ["/app/.venv/bin/python", "-m", "nextcloud_mcp_server.app", "--host", "0.0.0.0"]
