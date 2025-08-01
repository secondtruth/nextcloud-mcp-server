"""Base client for Nextcloud operations with shared authentication."""

import logging
from abc import ABC

from httpx import AsyncClient

logger = logging.getLogger(__name__)


class BaseNextcloudClient(ABC):
    """Base class for all Nextcloud app clients."""

    def __init__(self, http_client: AsyncClient, username: str):
        """Initialize with shared HTTP client and username.

        Args:
            http_client: Authenticated AsyncClient instance
            username: Nextcloud username for WebDAV operations
        """
        self._client = http_client
        self.username = username

    def _get_webdav_base_path(self) -> str:
        """Helper to get the base WebDAV path for the authenticated user."""
        return f"/remote.php/dav/files/{self.username}"

    async def _make_request(self, method: str, url: str, **kwargs):
        """Common request wrapper with logging and error handling.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters

        Returns:
            Response object
        """
        logger.debug(f"Making {method} request to {url}")
        response = await self._client.request(method, url, **kwargs)
        response.raise_for_status()
        return response
