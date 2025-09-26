import click
import logging
import os
import uvicorn
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, AsyncExitStack
from dataclasses import dataclass
from typing import Optional

from starlette.applications import Starlette
from starlette.routing import Mount

from mcp.server.fastmcp import Context, FastMCP

from nextcloud_mcp_server.config import setup_logging
from nextcloud_mcp_server.client import NextcloudClient
from nextcloud_mcp_server.utils import get_nc_client
from nextcloud_mcp_server.server import (
    configure_calendar_tools,
    configure_contacts_tools,
    configure_notes_tools,
    configure_tables_tools,
    configure_webdav_tools,
    configure_deck_tools,
)


logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    client: Optional[NextcloudClient]  # None in multi-user mode
    nextcloud_host: str
    multi_user_mode: bool


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Check if multi-user mode is enabled
    multi_user_mode = os.environ.get("NCMCP_MULTI_USER", "false").lower() == "true"
    nextcloud_host = os.environ.get("NEXTCLOUD_HOST", "")
    
    if not nextcloud_host:
        raise ValueError("NEXTCLOUD_HOST environment variable is required")
    
    if multi_user_mode:
        # Multi-user mode: no global client, credentials come per-request
        logging.info("Starting in multi-user mode - credentials required per request")
        client = None
    else:
        # Single-user mode: create global client from env
        logging.info("Starting in single-user mode")
        client = NextcloudClient.from_env()
        logging.info("Client initialization wait complete.")
    
    try:
        yield AppContext(
            client=client,
            nextcloud_host=nextcloud_host,
            multi_user_mode=multi_user_mode
        )
    finally:
        # Cleanup on shutdown
        if client:
            await client.close()


def get_app(transport: str = "sse", enabled_apps: list[str] | None = None, multi_user: bool | None = None):
    setup_logging()

    # Create an MCP server
    mcp = FastMCP("Nextcloud MCP", lifespan=app_lifespan)

    @mcp.resource("nc://capabilities")
    async def nc_get_capabilities():
        """Get the Nextcloud Host capabilities"""
        ctx: Context = (
            mcp.get_context()
        )  # https://github.com/modelcontextprotocol/python-sdk/issues/244
        client: NextcloudClient = get_nc_client(ctx)
        return await client.capabilities()

    # Define available apps and their configuration functions
    available_apps = {
        "notes": configure_notes_tools,
        "tables": configure_tables_tools,
        "webdav": configure_webdav_tools,
        "calendar": configure_calendar_tools,
        "contacts": configure_contacts_tools,
        "deck": configure_deck_tools,
    }

    # If no specific apps are specified, enable all
    if enabled_apps is None:
        enabled_apps = list(available_apps.keys())

    # Configure only the enabled apps
    for app_name in enabled_apps:
        if app_name in available_apps:
            logger.info(f"Configuring {app_name} tools")
            available_apps[app_name](mcp)
        else:
            logger.warning(
                f"Unknown app: {app_name}. Available apps: {list(available_apps.keys())}"
            )

    if transport == "sse":
        mcp_app = mcp.sse_app()
        lifespan = None
        app = Starlette(routes=[Mount("/", app=mcp_app)], lifespan=lifespan)
    elif transport in ("http", "streamable-http"):
        mcp_app = mcp.streamable_http_app()

        @asynccontextmanager
        async def lifespan(app: Starlette):
            async with AsyncExitStack() as stack:
                await stack.enter_async_context(mcp.session_manager.run())
                yield

        app = Starlette(routes=[Mount("/", app=mcp_app)], lifespan=lifespan)
        
        # Add multi-user middleware if enabled
        # CLI flag takes precedence over environment variable
        if multi_user is not None:
            multi_user_mode = multi_user
        else:
            multi_user_mode = os.environ.get("NCMCP_MULTI_USER", "false").lower() == "true"
        
        if multi_user_mode:
            from nextcloud_mcp_server.middleware import MultiUserAuthMiddleware
            nextcloud_host = os.environ.get("NEXTCLOUD_HOST", "")
            if not nextcloud_host:
                raise ValueError("NEXTCLOUD_HOST environment variable is required for multi-user mode")
            app.add_middleware(MultiUserAuthMiddleware, nextcloud_host=nextcloud_host)

    return app


@click.command()
@click.option("--host", "-h", default="127.0.0.1", show_default=True)
@click.option("--port", "-p", type=int, default=8000, show_default=True)
@click.option("--workers", "-w", type=int, default=None)
@click.option("--reload", "-r", is_flag=True)
@click.option(
    "--log-level",
    "-l",
    default="info",
    show_default=True,
    type=click.Choice(["critical", "error", "warning", "info", "debug", "trace"]),
)
@click.option(
    "--transport",
    "-t",
    default="sse",
    show_default=True,
    type=click.Choice(["sse", "streamable-http", "http"]),
)
@click.option(
    "--enable-app",
    "-e",
    multiple=True,
    type=click.Choice(["notes", "tables", "webdav", "calendar", "contacts", "deck"]),
    help="Enable specific Nextcloud app APIs. Can be specified multiple times. If not specified, all apps are enabled.",
)
@click.option(
    "--multi-user",
    is_flag=True,
    help="Enable multi-user mode with per-request authentication. Takes precedence over NCMCP_MULTI_USER environment variable.",
)
def run(
    host: str,
    port: int,
    workers: int,
    reload: bool,
    log_level: str,
    transport: str,
    enable_app: tuple[str, ...],
    multi_user: bool,
):
    enabled_apps = list(enable_app) if enable_app else None
    
    # Set environment variable if CLI flag is provided (takes precedence)
    if multi_user:
        os.environ["NCMCP_MULTI_USER"] = "true"

    if reload or workers:
        app = "nextcloud_mcp_server.app:get_app"
        factory = True
    else:
        app = get_app(transport=transport, enabled_apps=enabled_apps, multi_user=multi_user)
        factory = False

    uvicorn.run(
        app=app,
        factory=factory,
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=log_level,
    )


if __name__ == "__main__":
    run()
