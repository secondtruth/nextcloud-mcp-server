FROM ghcr.io/astral-sh/uv:0.8.12-python3.11-alpine@sha256:86701b128d1264e4908f82055069f9d483c6a99b44c14b49ce72a4bfc1de561d

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

CMD ["/app/.venv/bin/mcp", "run", "--transport", "sse", "/app/nextcloud_mcp_server/app.py:mcp"]
