FROM ghcr.io/astral-sh/uv:0.7.11-python3.11-alpine@sha256:66d4d13288afecfeb2173b267a6c0765957d2122935c447d6963ea7b38929a99

WORKDIR /app

COPY . .

RUN uv sync --locked

CMD ["uv", "run", "--locked", "mcp", "run", "--transport", "sse", "nextcloud_mcp_server/server.py:mcp"]
