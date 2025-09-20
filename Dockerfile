FROM ghcr.io/astral-sh/uv:0.8.19-python3.11-alpine@sha256:f55e8bf10a21798bee13afc9d12f6923e32d5557528d3368a6e7248aae201e84

WORKDIR /app

COPY . .

RUN uv sync --locked --no-dev

ENTRYPOINT ["/app/.venv/bin/nextcloud-mcp-server", "--host", "0.0.0.0"]
