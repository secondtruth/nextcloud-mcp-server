import logging
from nextcloud_mcp_server.config import setup_logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP, Context
from nextcloud_mcp_server.client import NextcloudClient
from collections.abc import AsyncIterator

from nextcloud_mcp_server.server.notes import configure_notes_tools
from nextcloud_mcp_server.server.tables import configure_tables_tools
from nextcloud_mcp_server.server.webdav import configure_webdav_tools

setup_logging()


@dataclass
class AppContext:
    client: NextcloudClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    logging.info("Creating Nextcloud client")
    client = NextcloudClient.from_env()
    logging.info("Client initialization wait complete.")
    try:
        yield AppContext(client=client)
    finally:
        # Cleanup on shutdown
        await client.close()


# Create an MCP server
mcp = FastMCP("Nextcloud MCP", lifespan=app_lifespan)

logger = logging.getLogger(__name__)


@mcp.resource("nc://capabilities")
async def nc_get_capabilities():
    """Get the Nextcloud Host capabilities"""
    ctx: Context = (
        mcp.get_context()
    )  # https://github.com/modelcontextprotocol/python-sdk/issues/244
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.capabilities()


configure_notes_tools(mcp)
configure_tables_tools(mcp)
configure_webdav_tools(mcp)


def run():
    mcp.run()


# if __name__ == "__main__":
# logger.info("Starting now")
# mcp.run()
