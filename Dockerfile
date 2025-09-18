FROM ghcr.io/astral-sh/uv:0.8.18-python3.11-alpine@sha256:368af158c1cf243aa7c518ca5d4772a1133f78df9100544868d58abe7a258ff8

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

ENTRYPOINT ["/app/.venv/bin/python", "-m", "nextcloud_mcp_server.app", "--host", "0.0.0.0"]
