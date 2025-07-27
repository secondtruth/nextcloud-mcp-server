import logging
from mcp.server.fastmcp import FastMCP, Context
from nextcloud_mcp_server.client import NextcloudClient

logger = logging.getLogger(__name__)


def configure_notes_tools(mcp: FastMCP):
    @mcp.resource("notes://settings")
    async def notes_get_settings():
        """Get the Notes App settings"""
        ctx: Context = (
            mcp.get_context()
        )  # https://github.com/modelcontextprotocol/python-sdk/issues/244
        client: NextcloudClient = ctx.request_context.lifespan_context.client
        return await client.notes.get_settings()

    @mcp.resource("nc://Notes/{note_id}/attachments/{attachment_filename}")
    async def nc_notes_get_attachment(note_id: int, attachment_filename: str):
        """Get a specific attachment from a note"""
        ctx: Context = mcp.get_context()
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

    @mcp.tool()
    async def nc_get_note(note_id: int, ctx: Context):
        """Get user note using note id"""
        client: NextcloudClient = ctx.request_context.lifespan_context.client
        return await client.notes.get_note(note_id)

    @mcp.tool()
    async def nc_notes_create_note(
        title: str, content: str, category: str, ctx: Context
    ):
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
