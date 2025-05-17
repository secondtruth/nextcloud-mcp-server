FROM ghcr.io/astral-sh/uv:python3.11-alpine@sha256:4d7283722d2d46d6789acc03e95e0bf13a99996fa01803707d877f85643da458

WORKDIR /app

COPY . .

RUN uv sync --locked

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV FASTMCP_LOG_LEVEL=DEBUG

CMD ["mcp", "run", "--transport", "sse", "nextcloud_mcp_server/server.py:mcp"]
