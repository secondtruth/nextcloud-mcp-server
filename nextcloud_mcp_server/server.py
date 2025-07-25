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
    ctx: Context = (
        mcp.get_context()
    )  # https://github.com/modelcontextprotocol/python-sdk/issues/244
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.capabilities()


@mcp.resource("notes://settings")
async def notes_get_settings():
    """Get the Notes App settings"""
    ctx: Context = (
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
    ctx: Context,
    limit: int | None = None,
    offset: int | None = None,
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


# WebDAV file system tools
@mcp.tool()
async def nc_webdav_list_directory(ctx: Context, path: str = ""):
    """List files and directories in the specified NextCloud path.
    
    Args:
        path: Directory path to list (empty string for root directory)
        
    Returns:
        List of items with metadata including name, path, is_directory, size, content_type, last_modified
        
    Examples:
        # List root directory
        await nc_webdav_list_directory("")
        
        # List a specific folder
        await nc_webdav_list_directory("Documents/Projects")
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.webdav.list_directory(path)


@mcp.tool()
async def nc_webdav_read_file(path: str, ctx: Context):
    """Read the content of a file from NextCloud.
    
    Args:
        path: Full path to the file to read
        
    Returns:
        Dict with path, content, content_type, size, and encoding (if binary)
        Text files are decoded to UTF-8, binary files are base64 encoded
        
    Examples:
        # Read a text file
        result = await nc_webdav_read_file("Documents/readme.txt")
        print(result['content'])  # Decoded text content
        
        # Read a binary file
        result = await nc_webdav_read_file("Images/photo.jpg")
        print(result['encoding'])  # 'base64'
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    content, content_type = await client.webdav.read_file(path)
    
    # For text files, decode content for easier viewing
    if content_type and content_type.startswith("text/"):
        try:
            decoded_content = content.decode("utf-8")
            return {
                "path": path,
                "content": decoded_content,
                "content_type": content_type,
                "size": len(content)
            }
        except UnicodeDecodeError:
            pass
    
    # For binary files, return metadata and base64 encoded content
    import base64
    return {
        "path": path,
        "content": base64.b64encode(content).decode("ascii"),
        "content_type": content_type,
        "size": len(content),
        "encoding": "base64"
    }


@mcp.tool()
async def nc_webdav_write_file(path: str, content: str, ctx: Context, content_type: str | None = None):
    """Write content to a file in NextCloud.
    
    Args:
        path: Full path where to write the file
        content: File content (text or base64 for binary)
        content_type: MIME type (auto-detected if not provided, use 'type;base64' for binary)
        
    Returns:
        Dict with status_code indicating success
        
    Examples:
        # Write a text file
        await nc_webdav_write_file("Documents/notes.md", "# My Notes\nContent here...")
        
        # Write binary data (base64 encoded)
        await nc_webdav_write_file("files/data.bin", base64_content, "application/octet-stream;base64")
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    
    # Handle base64 encoded content
    if content_type and "base64" in content_type.lower():
        import base64
        content_bytes = base64.b64decode(content)
        content_type = content_type.replace(";base64", "")
    else:
        content_bytes = content.encode("utf-8")
    
    return await client.webdav.write_file(path, content_bytes, content_type)


@mcp.tool()
async def nc_webdav_create_directory(path: str, ctx: Context):
    """Create a directory in NextCloud.
    
    Args:
        path: Full path of the directory to create
        
    Returns:
        Dict with status_code (201 for created, 405 if already exists)
        
    Examples:
        # Create a single directory
        await nc_webdav_create_directory("NewProject")
        
        # Create nested directories (parent must exist)
        await nc_webdav_create_directory("Projects/MyApp/docs")
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.webdav.create_directory(path)


@mcp.tool()
async def nc_webdav_delete_resource(path: str, ctx: Context):
    """Delete a file or directory in NextCloud.
    
    Args:
        path: Full path of the file or directory to delete
        
    Returns:
        Dict with status_code indicating result (404 if not found)
        
    Examples:
        # Delete a file
        await nc_webdav_delete_resource("old_document.txt")
        
        # Delete a directory (will delete all contents)
        await nc_webdav_delete_resource("temp_folder")
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.webdav.delete_resource(path)


def run():
    mcp.run()


if __name__ == "__main__":
    logger.info("Starting now")
    mcp.run()
