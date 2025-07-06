import os
from httpx import (
    AsyncClient,
    Auth,
    BasicAuth,
    Request,
    Response,
)
import logging

from .notes_client import NotesClient
from .webdav_client import WebDAVClient
from .controllers.notes_search import NotesSearchController

logger = logging.getLogger(__name__)


def log_request(request: Request):
    logger.info(
        "Request event hook: %s %s - Waiting for content",
        request.method,
        request.url,
    )
    logger.info("Request body: %s", request.content)
    logger.info("Headers: %s", request.headers)


def log_response(response: Response):
    response.read()  # Explicitly read the stream before accessing .text
    logger.info("Response [%s] %s", response.status_code, response.text)


class NextcloudClient:
    """Main Nextcloud client that orchestrates all app clients."""
    
    def __init__(self, base_url: str, username: str, auth: Auth | None = None):
        self.username = username
        self._client = AsyncClient(
            base_url=base_url,
            auth=auth,
            # event_hooks={"request": [log_request], "response": [log_response]},
        )
        
        # Initialize app clients
        self.notes = NotesClient(self._client, username)
        self.webdav = WebDAVClient(self._client, username)
        
        # Initialize controllers
        self._notes_search = NotesSearchController()

    @classmethod
    def from_env(cls):
        logger.info("Creating NC Client using env vars")

        host = os.environ["NEXTCLOUD_HOST"]
        username = os.environ["NEXTCLOUD_USERNAME"]
        password = os.environ["NEXTCLOUD_PASSWORD"]
        # Pass username to constructor
        return cls(base_url=host, username=username, auth=BasicAuth(username, password))

    async def capabilities(self):
        response = await self._client.get(
            "/ocs/v2.php/cloud/capabilities",
            headers={"OCS-APIRequest": "true", "Accept": "application/json"},
        )
        response.raise_for_status()

        return response.json()

    # Convenience methods that delegate to subclients
    async def notes_get_settings(self):
        """Get Notes app settings."""
        return await self.notes.get_settings()

    async def notes_get_all(self):
        """Get all notes."""
        return await self.notes.get_all_notes()

    async def notes_get_note(self, *, note_id: int):
        """Get a specific note."""
        return await self.notes.get_note(note_id)

    async def notes_create_note(
        self,
        *,
        title: str | None = None,
        content: str | None = None,
        category: str | None = None,
    ):
        """Create a new note."""
        return await self.notes.create_note(title=title, content=content, category=category)

    async def notes_update_note(
        self,
        *,
        note_id: int,
        etag: str,
        title: str | None = None,
        content: str | None = None,
        category: str | None = None,
    ):
        """Update a note."""
        return await self.notes.update(
            note_id=note_id, etag=etag, title=title, content=content, category=category
        )

    async def notes_append_content(self, *, note_id: int, content: str):
        """Append content to an existing note with a separator."""
        return await self.notes.append_content(note_id=note_id, content=content)

    async def notes_search_notes(self, *, query: str):
        """Search notes using token-based matching with relevance ranking."""
        all_notes = await self.notes.get_all_notes()
        return self._notes_search.search_notes(all_notes, query)


    async def notes_delete_note(self, *, note_id: int):
        """Delete a note and its attachments."""
        return await self.notes.delete_note(note_id)

    async def add_note_attachment(
        self,
        *,
        note_id: int,
        filename: str,
        content: bytes,
        category: str | None = None,
        mime_type: str | None = None,
    ):
        """Add/Update an attachment to a note via WebDAV PUT."""
        return await self.webdav.add_note_attachment(
            note_id=note_id,
            filename=filename,
            content=content,
            category=category,
            mime_type=mime_type,
        )

    async def get_note_attachment(
        self, *, note_id: int, filename: str, category: str | None = None
    ):
        """Fetch a specific attachment from a note via WebDAV GET."""
        return await self.webdav.get_note_attachment(
            note_id=note_id, filename=filename, category=category
        )

    def _get_webdav_base_path(self) -> str:
        """Helper to get the base WebDAV path for the authenticated user."""
        return f"/remote.php/dav/files/{self.username}"

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
