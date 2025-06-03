FROM ghcr.io/astral-sh/uv:0.7.10-python3.11-alpine@sha256:dfbf9f14b625e7f9818e5d01d0f35372cad0a408e85c5ee13e0938d3a04ba1c7

WORKDIR /app

COPY . .

RUN uv sync --locked

CMD ["uv", "run", "--locked", "mcp", "run", "--transport", "sse", "nextcloud_mcp_server/server.py:mcp"]
