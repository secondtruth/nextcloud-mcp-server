FROM ghcr.io/astral-sh/uv:python3.11-alpine@sha256:c77e10ca22ef1021e1cafcbaee9595b5f9d8d9f2b1fe4cc7e908b981bab73ee7

WORKDIR /app

COPY . .

RUN uv sync --locked

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV FASTMCP_LOG_LEVEL=DEBUG

CMD ["mcp", "run", "--transport", "sse", "nextcloud_mcp_server/server.py:mcp"]
