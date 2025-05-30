FROM ghcr.io/astral-sh/uv:0.7.9-python3.11-alpine@sha256:e1656fff9e032ceb7c267ca258d2cea5f6579ce31fc8df234284d7fb421f7a4e

WORKDIR /app

COPY . .

RUN uv sync --locked

CMD ["uv", "run", "--locked", "mcp", "run", "--transport", "sse", "nextcloud_mcp_server/server.py:mcp"]
