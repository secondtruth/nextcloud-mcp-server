FROM ghcr.io/astral-sh/uv:python3.11-alpine@sha256:94b38a25abdfa08a8493c78873475a470c460b800f4c22d73a266e8975ba24dc

WORKDIR /app

COPY . .

RUN uv sync --locked

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV FASTMCP_LOG_LEVEL=DEBUG

CMD ["mcp", "run", "--transport", "sse", "nextcloud_mcp_server/server.py:mcp"]
