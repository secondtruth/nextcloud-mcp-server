FROM ghcr.io/astral-sh/uv:0.7.8-python3.11-alpine@sha256:e7a2eb4196da4b1cc8c746c3fd7209b8c3682aeb679b87e63382c9e2000a9b29

WORKDIR /app

COPY . .

RUN uv sync --locked

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV FASTMCP_LOG_LEVEL=DEBUG

CMD ["mcp", "run", "--transport", "sse", "nextcloud_mcp_server/server.py:mcp"]
