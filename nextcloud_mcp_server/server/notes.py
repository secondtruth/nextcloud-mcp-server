import logging
from httpx import HTTPStatusError
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData

from mcp.server.fastmcp import Context, FastMCP

from nextcloud_mcp_server.client import NextcloudClient
from nextcloud_mcp_server.utils import get_nc_client
from nextcloud_mcp_server.models.notes import (
    Note,
    NotesSettings,
    CreateNoteResponse,
    UpdateNoteResponse,
    DeleteNoteResponse,
    AppendContentResponse,
    SearchNotesResponse,
    NoteSearchResult,
)

logger = logging.getLogger(__name__)


def configure_notes_tools(mcp: FastMCP):
    @mcp.resource("notes://settings")
    async def notes_get_settings():
        """Get the Notes App settings"""
        ctx: Context = (
            mcp.get_context()
        )  # https://github.com/modelcontextprotocol/python-sdk/issues/244
        client: NextcloudClient = get_nc_client(ctx)
        settings_data = await client.notes.get_settings()
        return NotesSettings(**settings_data)

    @mcp.resource("nc://Notes/{note_id}/attachments/{attachment_filename}")
    async def nc_notes_get_attachment_resource(note_id: int, attachment_filename: str):
        """Get a specific attachment from a note"""
        ctx: Context = mcp.get_context()
        client: NextcloudClient = get_nc_client(ctx)
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

    @mcp.resource("nc://Notes/{note_id}")
    async def nc_get_note_resource(note_id: int):
        """Get user note using note id"""

        ctx: Context = mcp.get_context()
        client: NextcloudClient = get_nc_client(ctx)
        try:
            note_data = await client.notes.get_note(note_id)
            return Note(**note_data)
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                raise McpError(ErrorData(code=-1, message=f"Note {note_id} not found"))
            elif e.response.status_code == 403:
                raise McpError(
                    ErrorData(code=-1, message=f"Access denied to note {note_id}")
                )
            else:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Failed to retrieve note {note_id}: {e.response.reason_phrase}",
                    )
                )

    @mcp.tool()
    async def nc_notes_create_note(
        title: str, content: str, category: str, ctx: Context
    ) -> CreateNoteResponse:
        """Create a new note"""
        client: NextcloudClient = get_nc_client(ctx)
        try:
            note_data = await client.notes.create_note(
                title=title,
                content=content,
                category=category,
            )
            note = Note(**note_data)
            return CreateNoteResponse(
                id=note.id, title=note.title, category=note.category, etag=note.etag
            )
        except HTTPStatusError as e:
            if e.response.status_code == 403:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message="Access denied: insufficient permissions to create notes",
                    )
                )
            elif e.response.status_code == 413:
                raise McpError(ErrorData(code=-1, message="Note content too large"))
            elif e.response.status_code == 409:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"A note with title '{title}' already exists in this category",
                    )
                )
            else:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Failed to create note: server error ({e.response.status_code})",
                    )
                )

    @mcp.tool()
    async def nc_notes_update_note(
        note_id: int,
        etag: str,
        title: str | None,
        content: str | None,
        category: str | None,
        ctx: Context,
    ) -> UpdateNoteResponse:
        """Update an existing note's title, content, or category.

        REQUIRED: etag parameter must be provided to prevent overwriting concurrent changes.
        Get the current ETag by first retrieving the note using nc_notes_get_note tool.
        If the note has been modified by someone else since you retrieved it,
        the update will fail with a 412 error."""
        logger.info("Updating note %s", note_id)
        client: NextcloudClient = get_nc_client(ctx)
        try:
            note_data = await client.notes.update(
                note_id=note_id,
                etag=etag,
                title=title,
                content=content,
                category=category,
            )
            note = Note(**note_data)
            return UpdateNoteResponse(
                id=note.id, title=note.title, category=note.category, etag=note.etag
            )
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                raise McpError(ErrorData(code=-1, message=f"Note {note_id} not found"))
            elif e.response.status_code == 412:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Note {note_id} has been modified by someone else. Please refresh and try again.",
                    )
                )
            elif e.response.status_code == 403:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Access denied: insufficient permissions to update note {note_id}",
                    )
                )
            elif e.response.status_code == 413:
                raise McpError(
                    ErrorData(code=-1, message="Updated note content is too large")
                )
            else:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Failed to update note {note_id}: server error ({e.response.status_code})",
                    )
                )

    @mcp.tool()
    async def nc_notes_append_content(
        note_id: int, content: str, ctx: Context
    ) -> AppendContentResponse:
        """Append content to an existing note. The tool adds a `\n---\n`
        between the note and what will be appended."""

        logger.info("Appending content to note %s", note_id)
        client: NextcloudClient = get_nc_client(ctx)
        try:
            note_data = await client.notes.append_content(
                note_id=note_id, content=content
            )
            note = Note(**note_data)
            return AppendContentResponse(
                id=note.id, title=note.title, category=note.category, etag=note.etag
            )
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                raise McpError(ErrorData(code=-1, message=f"Note {note_id} not found"))
            elif e.response.status_code == 403:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Access denied: insufficient permissions to modify note {note_id}",
                    )
                )
            elif e.response.status_code == 413:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message="Content to append would make the note too large",
                    )
                )
            else:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Failed to append content to note {note_id}: server error ({e.response.status_code})",
                    )
                )

    @mcp.tool()
    async def nc_notes_search_notes(query: str, ctx: Context) -> SearchNotesResponse:
        """Search notes by title or content, returning only id, title, and category."""
        client: NextcloudClient = get_nc_client(ctx)
        try:
            search_results_raw = await client.notes_search_notes(query=query)

            # Convert to NoteSearchResult models, including the _score field
            results = [
                NoteSearchResult(
                    id=result["id"],
                    title=result["title"],
                    category=result["category"],
                    score=result.get("_score"),  # Include search score if available
                )
                for result in search_results_raw
            ]

            return SearchNotesResponse(
                results=results, query=query, total_found=len(results)
            )
        except HTTPStatusError as e:
            if e.response.status_code == 403:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message="Access denied: insufficient permissions to search notes",
                    )
                )
            elif e.response.status_code == 400:
                raise McpError(
                    ErrorData(code=-1, message="Invalid search query format")
                )
            else:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Search failed: server error ({e.response.status_code})",
                    )
                )

    @mcp.tool()
    async def nc_notes_get_note(note_id: int, ctx: Context) -> Note:
        """Get a specific note by its ID"""
        client: NextcloudClient = get_nc_client(ctx)
        try:
            note_data = await client.notes.get_note(note_id)
            return Note(**note_data)
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                raise McpError(ErrorData(code=-1, message=f"Note {note_id} not found"))
            elif e.response.status_code == 403:
                raise McpError(
                    ErrorData(code=-1, message=f"Access denied to note {note_id}")
                )
            else:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Failed to retrieve note {note_id}: {e.response.reason_phrase}",
                    )
                )

    @mcp.tool()
    async def nc_notes_get_attachment(
        note_id: int, attachment_filename: str, ctx: Context
    ) -> dict[str, str]:
        """Get a specific attachment from a note"""
        client: NextcloudClient = get_nc_client(ctx)
        try:
            content, mime_type = await client.webdav.get_note_attachment(
                note_id=note_id, filename=attachment_filename
            )
            return {
                "uri": f"nc://Notes/{note_id}/attachments/{attachment_filename}",
                "mimeType": mime_type,
                "data": content,
            }
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Attachment {attachment_filename} not found for note {note_id}",
                    )
                )
            elif e.response.status_code == 403:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Access denied to attachment {attachment_filename} for note {note_id}",
                    )
                )
            else:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Failed to retrieve attachment: {e.response.reason_phrase}",
                    )
                )

    @mcp.tool()
    async def nc_notes_delete_note(note_id: int, ctx: Context) -> DeleteNoteResponse:
        """Delete a note permanently"""
        logger.info("Deleting note %s", note_id)
        client: NextcloudClient = get_nc_client(ctx)
        try:
            await client.notes.delete_note(note_id)
            return DeleteNoteResponse(
                status_code=200,
                message=f"Note {note_id} deleted successfully",
                deleted_id=note_id,
            )
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                raise McpError(ErrorData(code=-1, message=f"Note {note_id} not found"))
            elif e.response.status_code == 403:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Access denied: insufficient permissions to delete note {note_id}",
                    )
                )
            else:
                raise McpError(
                    ErrorData(
                        code=-1,
                        message=f"Failed to delete note {note_id}: server error ({e.response.status_code})",
                    )
                )
