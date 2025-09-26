import logging
import os

from httpx import (
    AsyncClient,
    Auth,
    BasicAuth,
    Request,
    Response,
    AsyncBaseTransport,
    AsyncHTTPTransport,
)

from ..controllers.notes_search import NotesSearchController
from .calendar import CalendarClient
from .contacts import ContactsClient
from .deck import DeckClient
from .notes import NotesClient
from .tables import TablesClient
from .webdav import WebDAVClient

logger = logging.getLogger(__name__)


async def log_request(request: Request):
    # Redact authorization headers for security
    safe_headers = dict(request.headers)
    if "authorization" in safe_headers:
        safe_headers["authorization"] = "[REDACTED]"
    
    logger.debug(
        "Request event hook: %s %s - Waiting for content",
        request.method,
        request.url,
    )
    logger.debug("Request body: %s", request.content)
    logger.debug("Headers: %s", safe_headers)


async def log_response(response: Response):
    await response.aread()
    logger.debug("Response [%s] %s", response.status_code, response.text)


class AsyncDisableCookieTransport(AsyncBaseTransport):
    """This Transport disable cookies from accumulating in the httpx AsyncClient

    Thanks to: https://github.com/encode/httpx/issues/2992#issuecomment-2133258994
    """

    def __init__(self, transport: AsyncBaseTransport):
        self.transport = transport

    async def handle_async_request(self, request: Request) -> Response:
        response = await self.transport.handle_async_request(request)
        response.headers.pop("set-cookie", None)
        return response


class NextcloudClient:
    """Main Nextcloud client that orchestrates all app clients."""

    def __init__(self, base_url: str, username: str, auth: Auth | None = None):
        self.username = username
        self._client = AsyncClient(
            base_url=base_url,
            auth=auth,
            transport=AsyncDisableCookieTransport(AsyncHTTPTransport()),
            event_hooks={"request": [log_request], "response": [log_response]},
        )

        # Initialize app clients
        self.notes = NotesClient(self._client, username)
        self.webdav = WebDAVClient(self._client, username)
        self.tables = TablesClient(self._client, username)
        self.calendar = CalendarClient(self._client, username)
        self.contacts = ContactsClient(self._client, username)
        self.deck = DeckClient(self._client, username)

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
