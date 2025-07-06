"""WebDAV client for Nextcloud file operations."""

import mimetypes
from typing import Tuple, Dict, Any, Optional
import logging
from httpx import HTTPStatusError

from .base import BaseNextcloudClient

logger = logging.getLogger(__name__)


class WebDAVClient(BaseNextcloudClient):
    """Client for Nextcloud WebDAV operations."""

    async def delete_resource(self, path: str) -> Dict[str, Any]:
        """Delete a resource (file or directory) via WebDAV DELETE."""
        # Ensure path ends with a slash if it's a directory
        if not path.endswith("/"):
            path_with_slash = f"{path}/"
        else:
            path_with_slash = path

        webdav_path = f"{self._get_webdav_base_path()}/{path_with_slash.lstrip('/')}"
        logger.info(f"Deleting WebDAV resource: {webdav_path}")

        headers = {"OCS-APIRequest": "true"}
        try:
            # First try a PROPFIND to verify resource exists
            propfind_headers = {"Depth": "0", "OCS-APIRequest": "true"}
            try:
                propfind_resp = await self._client.request(
                    "PROPFIND", webdav_path, headers=propfind_headers
                )
                logger.info(
                    f"Resource exists check (PROPFIND) status: {propfind_resp.status_code}"
                )
            except HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.info(
                        f"Resource '{webdav_path}' doesn't exist, no deletion needed."
                    )
                    return {"status_code": 404}
                # For other errors, continue with deletion attempt

            # Proceed with deletion
            response = await self._client.delete(webdav_path, headers=headers)
            response.raise_for_status()
            logger.info(
                f"Successfully deleted WebDAV resource '{webdav_path}' (Status: {response.status_code})"
            )
            return {"status_code": response.status_code}

        except HTTPStatusError as e:
            logger.warning(f"HTTP error deleting WebDAV resource '{webdav_path}': {e}")
            if e.response.status_code != 404:
                raise e
            else:
                logger.info(f"Resource '{webdav_path}' not found, no deletion needed.")
                return {"status_code": 404}
        except Exception as e:
            logger.warning(
                f"Unexpected error deleting WebDAV resource '{webdav_path}': {e}"
            )
            raise e

    async def cleanup_old_attachment_directory(
        self, note_id: int, old_category: str
    ) -> Dict[str, Any]:
        """Clean up the attachment directory for a note in its old category location."""
        old_category_path_part = f"{old_category}/" if old_category else ""
        old_attachment_dir_path = (
            f"Notes/{old_category_path_part}.attachments.{note_id}/"
        )

        logger.info(f"Cleaning up old attachment directory: {old_attachment_dir_path}")
        try:
            delete_result = await self.delete_resource(path=old_attachment_dir_path)
            logger.info(f"Cleanup of old attachment directory result: {delete_result}")
            return delete_result
        except Exception as e:
            logger.error(f"Error during cleanup of old attachment directory: {e}")
            raise e

    async def cleanup_note_attachments(
        self, note_id: int, category: str
    ) -> Dict[str, Any]:
        """Clean up attachment directory for a specific note and category."""
        cat_path_part = f"{category}/" if category else ""
        attachment_dir_path = f"Notes/{cat_path_part}.attachments.{note_id}/"

        logger.info(
            f"Attempting to delete attachment directory for note {note_id} in category '{category}' via WebDAV: {attachment_dir_path}"
        )
        try:
            delete_result = await self.delete_resource(path=attachment_dir_path)
            logger.info(
                f"WebDAV deletion for category '{category}' attachment directory: {delete_result}"
            )
            return delete_result
        except Exception as e:
            logger.warning(
                f"Failed during WebDAV deletion for category '{category}' attachment directory: {e}"
            )
            raise e

    async def add_note_attachment(
        self,
        note_id: int,
        filename: str,
        content: bytes,
        category: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add/Update an attachment to a note via WebDAV PUT."""
        # Construct paths based on provided category
        webdav_base = self._get_webdav_base_path()
        category_path_part = f"{category}/" if category else ""
        attachment_dir_segment = f".attachments.{note_id}"
        parent_dir_webdav_rel_path = (
            f"Notes/{category_path_part}{attachment_dir_segment}"
        )
        parent_dir_path = f"{webdav_base}/{parent_dir_webdav_rel_path}"
        attachment_path = f"{parent_dir_path}/{filename}"

        logger.info(
            f"Uploading attachment for note {note_id} (category: '{category or ''}') to WebDAV path: {attachment_path}"
        )

        # Log current auth settings
        logger.info(
            f"WebDAV auth settings - Username: {self.username}, Auth Type: {type(self._client.auth).__name__}"
        )

        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream"

        headers = {"Content-Type": mime_type, "OCS-APIRequest": "true"}
        try:
            # First check if we can access WebDAV at all
            notes_dir_path = f"{webdav_base}/Notes"
            logger.info(f"Testing WebDAV access to Notes directory: {notes_dir_path}")

            propfind_headers = {"Depth": "0", "OCS-APIRequest": "true"}
            notes_dir_response = await self._client.request(
                "PROPFIND", notes_dir_path, headers=propfind_headers
            )

            if notes_dir_response.status_code == 401:
                logger.error(
                    "WebDAV authentication failed for Notes directory. Please verify WebDAV permissions."
                )
                raise HTTPStatusError(
                    f"Authentication error accessing WebDAV Notes directory: {notes_dir_response.status_code}",
                    request=notes_dir_response.request,
                    response=notes_dir_response,
                )
            elif notes_dir_response.status_code >= 400:
                logger.error(
                    f"Error accessing WebDAV Notes directory: {notes_dir_response.status_code}"
                )
                notes_dir_response.raise_for_status()
            else:
                logger.info(
                    f"Successfully accessed WebDAV Notes directory (Status: {notes_dir_response.status_code})"
                )

            # Ensure the parent directory exists using MKCOL
            logger.info(f"Ensuring attachments directory exists: {parent_dir_path}")
            mkcol_headers = {"OCS-APIRequest": "true"}
            mkcol_response = await self._client.request(
                "MKCOL", parent_dir_path, headers=mkcol_headers
            )

            # MKCOL should return 201 Created or 405 Method Not Allowed (if directory already exists)
            if mkcol_response.status_code not in [201, 405]:
                logger.warning(
                    f"Unexpected status code {mkcol_response.status_code} when creating attachments directory"
                )
                mkcol_response.raise_for_status()
            else:
                logger.info(
                    f"Created/verified directory: {parent_dir_path} (Status: {mkcol_response.status_code})"
                )

            # Proceed with the PUT request
            logger.info(f"Putting attachment file to: {attachment_path}")
            response = await self._client.put(
                attachment_path, content=content, headers=headers
            )
            response.raise_for_status()
            logger.info(
                f"Successfully uploaded attachment '{filename}' to note {note_id} (Status: {response.status_code})"
            )
            return {"status_code": response.status_code}

        except HTTPStatusError as e:
            logger.error(
                f"HTTP error uploading attachment '{filename}' to note {note_id}: {e}"
            )
            raise e
        except Exception as e:
            logger.error(
                f"Unexpected error uploading attachment '{filename}' to note {note_id}: {e}"
            )
            raise e

    async def get_note_attachment(
        self, note_id: int, filename: str, category: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """Fetch a specific attachment from a note via WebDAV GET."""
        webdav_base = self._get_webdav_base_path()
        category_path_part = f"{category}/" if category else ""
        attachment_dir_segment = f".attachments.{note_id}"
        attachment_path = f"{webdav_base}/Notes/{category_path_part}{attachment_dir_segment}/{filename}"

        logger.info(
            f"Fetching attachment for note {note_id} (category: '{category or ''}') from WebDAV path: {attachment_path}"
        )

        try:
            response = await self._client.get(attachment_path)
            response.raise_for_status()

            content = response.content
            mime_type = response.headers.get("content-type", "application/octet-stream")

            logger.info(
                f"Successfully fetched attachment '{filename}' ({mime_type}, {len(content)} bytes)"
            )
            return content, mime_type

        except HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching attachment '{filename}' for note {note_id}: {e}"
            )
            raise e
        except Exception as e:
            logger.error(
                f"Unexpected error fetching attachment '{filename}' for note {note_id}: {e}"
            )
            raise e
