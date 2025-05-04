# server.py
import logging
from nextcloud_mcp_server.config import setup_logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP, Context
from mcp.server import Server
from collections.abc import AsyncIterator
from nextcloud_mcp_server.client import NextcloudClient

setup_logging()

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    client: NextcloudClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    logger.info("Creating Nextcloud client")
    client = NextcloudClient.from_env()
    try:
        yield AppContext(client=client)
    finally:
        # Cleanup on shutdown
        client._client.close()


# Create an MCP server
mcp = FastMCP("Nextcloud MCP", lifespan=app_lifespan)


@mcp.resource("nc://capabilities")
def nc_get_capabilities():
    """Get the Nextcloud Host capabilities"""
    # client = NextcloudClient.from_env()
    ctx = (
        mcp.get_context()
    )  # https://github.com/modelcontextprotocol/python-sdk/issues/244
    client = ctx.request_context.lifespan_context.client
    return client.capabilities()


@mcp.resource("notes://settings")
def notes_get_settings():
    """Get the Notes App settings"""
    ctx = (
        mcp.get_context()
    )  # https://github.com/modelcontextprotocol/python-sdk/issues/244
    client = ctx.request_context.lifespan_context.client
    return client.notes_get_settings()


@mcp.resource("notes://all")
def nc_notes_get_all():
    """Get all user notes"""
    ctx = (
        mcp.get_context()
    )  # https://github.com/modelcontextprotocol/python-sdk/issues/244
    client = ctx.request_context.lifespan_context.client
    return client.notes_get_all()


@mcp.resource("notes://{note_id}")
def nc_notes_get_note(note_id: int):
    """Get user note using note id"""
    ctx = (
        mcp.get_context()
    )  # https://github.com/modelcontextprotocol/python-sdk/issues/244
    client = ctx.request_context.lifespan_context.client
    return client.notes_get_note(note_id=note_id)


@mcp.tool()
def nc_notes_create_note(title: str, content: str, category: str, ctx: Context):
    """Create a new note"""
    client = ctx.request_context.lifespan_context.client
    return client.notes_create_note(
        title=title,
        content=content,
        category=category,
    )


@mcp.tool()
def nc_notes_update_note(
    note_id: int,
    etag: str,
    title: str | None,
    content: str | None,
    category: str | None,
    ctx: Context,
):
    logger.info("Updating note %s", note_id)
    client = ctx.request_context.lifespan_context.client
    return client.notes_update_note(
        note_id=note_id,
        etag=etag,
        title=title,
        content=content,
        category=category,
    )


@mcp.tool()
def nc_notes_delete_note(note_id: int, ctx: Context):
    logger.info("Deleting note %s", note_id)
    client = ctx.request_context.lifespan_context.client
    return client.notes_delete_note(note_id=note_id)


def run():
    mcp.run()


if __name__ == "__main__":
    logger.info("Starting now")
    mcp.run()
