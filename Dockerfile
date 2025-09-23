FROM ghcr.io/astral-sh/uv:0.8.22-python3.11-alpine@sha256:a8d5f7079a3223380ec060fefe48afe45b4c4622d631ce0e495593ac9a38f546

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

ENTRYPOINT ["/app/.venv/bin/nextcloud-mcp-server", "--host", "0.0.0.0"]
