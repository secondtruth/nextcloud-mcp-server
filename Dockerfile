FROM ghcr.io/astral-sh/uv:python3.11-alpine@sha256:2d9058ac1ecdd9b1baacae5362c8f40aa20137c6a1596e24eb956ff7469a9537

WORKDIR /app

COPY . .

RUN uv sync --locked

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV FASTMCP_LOG_LEVEL=DEBUG

CMD ["mcp", "run", "--transport", "sse", "nextcloud_mcp_server/server.py:mcp"]
