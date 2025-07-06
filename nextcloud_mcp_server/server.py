# server.py
import logging
from nextcloud_mcp_server.config import setup_logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP, Context
from collections.abc import AsyncIterator
from nextcloud_mcp_server.client import NextcloudClient

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
    ctx = (
        mcp.get_context()
    )  # https://github.com/modelcontextprotocol/python-sdk/issues/244
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.capabilities()


@mcp.resource("notes://settings")
async def notes_get_settings():
    """Get the Notes App settings"""
    ctx = (
        mcp.get_context()
    )  # https://github.com/modelcontextprotocol/python-sdk/issues/244
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.notes.get_settings()


@mcp.tool()
async def nc_get_note(note_id: int, ctx: Context):
    """Get user note using note id"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.notes.get_note(note_id)


@mcp.tool()
async def nc_notes_create_note(title: str, content: str, category: str, ctx: Context):
    """Create a new note"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.notes.create_note(
        title=title,
        content=content,
        category=category,
    )


@mcp.tool()
async def nc_notes_update_note(
    note_id: int,
    etag: str,
    title: str | None,
    content: str | None,
    category: str | None,
    ctx: Context,
):
    logger.info("Updating note %s", note_id)
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.notes.update(
        note_id=note_id,
        etag=etag,
        title=title,
        content=content,
        category=category,
    )


@mcp.tool()
async def nc_notes_append_content(note_id: int, content: str, ctx: Context):
    """Append content to an existing note with a clear separator"""
    logger.info("Appending content to note %s", note_id)
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.notes.append_content(note_id=note_id, content=content)


@mcp.tool()
async def nc_notes_search_notes(query: str, ctx: Context):
    """Search notes by title or content, returning only id, title, and category."""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.notes_search_notes(query=query)


@mcp.tool()
async def nc_notes_delete_note(note_id: int, ctx: Context):
    logger.info("Deleting note %s", note_id)
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.notes.delete_note(note_id)


# Tables tools
@mcp.tool()
async def nc_tables_list_tables(ctx: Context):
    """List all tables available to the user"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.tables.list_tables()


@mcp.tool()
async def nc_tables_get_schema(table_id: int, ctx: Context):
    """Get the schema/structure of a specific table including columns and views"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.tables.get_table_schema(table_id)


@mcp.tool()
async def nc_tables_read_table(
    table_id: int,
    limit: int | None = None,
    offset: int | None = None,
    ctx: Context = None,
):
    """Read rows from a table with optional pagination"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.tables.get_table_rows(table_id, limit, offset)


@mcp.tool()
async def nc_tables_insert_row(table_id: int, data: dict, ctx: Context):
    """Insert a new row into a table.

    Data should be a dictionary mapping column IDs to values, e.g. {1: "text", 2: 42}
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.tables.create_row(table_id, data)


@mcp.tool()
async def nc_tables_update_row(row_id: int, data: dict, ctx: Context):
    """Update an existing row in a table.

    Data should be a dictionary mapping column IDs to new values, e.g. {1: "new text", 2: 99}
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.tables.update_row(row_id, data)


@mcp.tool()
async def nc_tables_delete_row(row_id: int, ctx: Context):
    """Delete a row from a table"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.tables.delete_row(row_id)


@mcp.resource("nc://Notes/{note_id}/attachments/{attachment_filename}")
async def nc_notes_get_attachment(note_id: int, attachment_filename: str):
    """Get a specific attachment from a note"""
    ctx = mcp.get_context()
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    # Assuming a method get_note_attachment exists in the client
    # This method should return the raw content and determine the mime type
    content, mime_type = await client.webdav.get_note_attachment(
        note_id=note_id, filename=attachment_filename
    )
    return {
        "contents": [
            {
                # Use uppercase 'Notes' to match the decorator
                "uri": f"nc://Notes/{note_id}/attachments/{attachment_filename}",
                "mimeType": mime_type,  # Client needs to determine this
                "data": content,  # Return raw bytes/data
            }
        ]
    }


def run():
    mcp.run()


if __name__ == "__main__":
    logger.info("Starting now")
    mcp.run()
