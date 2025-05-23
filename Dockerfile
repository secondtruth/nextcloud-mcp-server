FROM ghcr.io/astral-sh/uv:python3.11-alpine@sha256:621987f3c300e222b71c6a2d8577382a28edc0dc1509969fc5865845f68b0863

WORKDIR /app

COPY . .

RUN uv sync --locked

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV FASTMCP_LOG_LEVEL=DEBUG

CMD ["mcp", "run", "--transport", "sse", "nextcloud_mcp_server/server.py:mcp"]
