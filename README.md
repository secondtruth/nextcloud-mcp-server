# Nextcloud MCP Server

The Nextcloud MCP server allows you to automate various actions on a Nextcloud instance via Large Language Models (LLMs) such as OpenAI, Gemini, etc.

To run the project locally, first make a copy of the `env.sample` file with your configuratoin. Then run the SSE server as follows:

```bash
$ source env.sample
$ mcp run --transport sse nextcloud_mcp_server/server.py:mcp
INFO:     Started server process [762644]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

or via a Docker container:

```bash
$ docker run -p 127.0.0.1:8000:8000 --env-file env.sample ghcr.io/cbcoutinho/nextcloud-mcp-server
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Once the server is running, you can connect to the server on port 8000 SSE/HTTP.

## Features

- Notes API: https://github.com/nextcloud/notes/blob/main/docs/api/README.md