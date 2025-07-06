import os
from httpx import (
    AsyncClient,
    Auth,
    BasicAuth,
    Request,
    Response,
)
import logging

from .notes import NotesClient
from .webdav import WebDAVClient
from .tables import TablesClient
from ..controllers.notes_search import NotesSearchController

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
        self.tables = TablesClient(self._client, username)

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

    async def notes_search_notes(self, *, query: str):
        """Search notes using token-based matching with relevance ranking."""
        all_notes = await self.notes.get_all_notes()
        return self._notes_search.search_notes(all_notes, query)

    def _get_webdav_base_path(self) -> str:
        """Helper to get the base WebDAV path for the authenticated user."""
        return f"/remote.php/dav/files/{self.username}"

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
