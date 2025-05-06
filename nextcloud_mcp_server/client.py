import os
import time  # Import time for sleep
import mimetypes
from io import BytesIO
from httpx import (
    Client,
    Auth,
    BasicAuth,
    Headers,
    Request,
    Response,
    HTTPStatusError,
)  # Import HTTPStatusError
import logging


logger = logging.getLogger(__name__)


def log_request(request: Request):
    logger.info(
        "Request event hook ****: %s %s - Waiting for content",
        request.method,
        request.url,
    )
    logger.info("Request body: %s", request.content)
    logger.info("Headers: %s", request.headers)


def log_response(response: Response):
    response.read()  # Explicitly read the stream before accessing .text
    logger.info("Response [%s] %s", response.status_code, response.text)


class NextcloudClient:

    def __init__(self, base_url: str, username: str, auth: Auth | None = None):
        self.username = username # Store username
        self._client = Client(
            base_url=base_url,
            auth=auth,
            event_hooks={"request": [log_request], "response": [log_response]},
        )

    @classmethod
    def from_env(cls):

        logger.info("Creating NC Client using env vars")

        host = os.environ["NEXTCLOUD_HOST"]
        username = os.environ["NEXTCLOUD_USERNAME"]
        password = os.environ["NEXTCLOUD_PASSWORD"]
        # Pass username to constructor
        return cls(base_url=host, username=username, auth=BasicAuth(username, password))

    def capabilities(self):

        response = self._client.get(
            "/ocs/v2.php/cloud/capabilities",
            headers={"OCS-APIRequest": "true", "Accept": "application/json"},
        )
        response.raise_for_status()

        return response.json()

    def notes_get_settings(self):
        response = self._client.get("/apps/notes/api/v1/settings")
        response.raise_for_status()
        return response.json()

    def notes_get_all(self):
        response = self._client.get("/apps/notes/api/v1/notes")
        response.raise_for_status()
        return response.json()

    def notes_get_note(self, *, note_id: int):
        response = self._client.get(f"/apps/notes/api/v1/notes/{note_id}")
        response.raise_for_status()
        return response.json()

    def notes_create_note(
        self,
        *,
        title: str | None = None,
        content: str | None = None,
        category: str | None = None,
    ):
        body = {}
        if title:
            body.update({"title": title})
        if content:
            body.update({"content": content})
        if category:
            body.update({"category": category})

        response = self._client.post(
            url="/apps/notes/api/v1/notes",
            json=body,
        )
        response.raise_for_status()
        return response.json()

    def notes_update_note(
        self,
        *,
        note_id: int,
        etag: str,
        title: str | None = None,
        content: str | None = None,
        category: str | None = None,
    ):
        # body = {"etag": etag} # Removed redundant line
        body = {}
        if title:
            body.update({"title": title})
        if content:
            body.update({"content": content})
        if category:
            body.update({"category": category})

        logger.info(
            "Attempting to update note %s with etag %s. Body: %s",
            note_id,
            etag,  # This was current_etag in the loop
            body,
        )
        # Ensure conditional PUT using If-Match header is active
        response = self._client.put(
            url=f"/apps/notes/api/v1/notes/{note_id}",
            json=body,
            headers={"If-Match": f'"{etag}"'},  # This was current_etag in the loop
        )
        logger.info(
            "Update response for note %s: Status %s, Headers %s",
            note_id,
            response.status_code,
            response.headers,
        )
        response.raise_for_status()
        return response.json()

    def notes_search_notes(self, *, query: str):
        all_notes = self.notes_get_all()
        search_results = []
        query_lower = query.lower()
        for note in all_notes:
            title_lower = note.get("title", "").lower()
            content_lower = note.get("content", "").lower()
            if query_lower in title_lower or query_lower in content_lower:
                search_results.append(
                    {
                        "id": note.get("id"),
                        "title": note.get("title"),
                        "category": note.get("category"),
                        "modified": note.get("modified"),
                    }
                )
        return search_results

    def notes_delete_note(self, *, note_id: int):
        # First delete the note through the Notes API
        response = self._client.delete(f"/apps/notes/api/v1/notes/{note_id}")
        response.raise_for_status()
        json_response = response.json()
        
        # Then try to delete the attachments directory via WebDAV
        try:
            webdav_base = self._get_webdav_base_path()
            attachments_dir = f"{webdav_base}/Notes/.attachments.{note_id}"
            logger.info("Deleting attachment directory: %s", attachments_dir)
            
            delete_response = self._client.request("DELETE", attachments_dir)
            # 204 No Content = successful delete, 404 Not Found = already gone (both OK)
            if delete_response.status_code not in [204, 404]:
                logger.warning(
                    "Unexpected status code %s when deleting attachments directory for note %s",
                    delete_response.status_code,
                    note_id
                )
                
                # In production, we should not raise an error if the Notes API deletion was successful
                # but WebDAV cleanup failed - this would leave the note inaccessible to users.
                # Instead, log the issue for admin attention.
                if delete_response.status_code == 401:
                    logger.error(
                        "Authentication error when trying to delete attachment directory for note %s. "
                        "Please verify WebDAV permissions.",
                        note_id
                    )
                elif delete_response.status_code >= 400:
                    logger.error(
                        "Error (HTTP %s) when trying to delete attachment directory for note %s.",
                        delete_response.status_code,
                        note_id
                    )
        except Exception as e:
            # Log but don't fail the operation if attachments cleanup fails
            logger.error(
                "Error cleaning up attachments directory for note %s: %s",
                note_id,
                e
            )
        
        return json_response

    # Removed incorrect get_note_attachment method that used Notes API

    def _get_webdav_base_path(self) -> str:
        """Helper to get the base WebDAV path for the authenticated user."""
        # Use the stored username
        return f"/remote.php/dav/files/{self.username}"

    def add_note_attachment(self, *, note_id: int, filename: str, content: bytes, mime_type: str | None = None):
        """Add/Update an attachment to a note via WebDAV PUT."""
        # Attachments are stored in a hidden folder .attachments.{note_id} within the Notes folder
        webdav_base = self._get_webdav_base_path()
        attachment_path = f"{webdav_base}/Notes/.attachments.{note_id}/{filename}"
        logger.info("Uploading attachment to WebDAV path: %s", attachment_path)
        
        # Log current auth settings to diagnose the issue
        logger.info("WebDAV auth settings - Username: %s, Auth Type: %s", 
                   self.username, type(self._client.auth).__name__)

        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream" # Default if guessing fails

        headers = {"Content-Type": mime_type}
        try:
            # First check if we can access WebDAV at all with current credentials
            # by checking the Notes directory
            notes_dir_path = f"{webdav_base}/Notes"
            logger.info("Testing WebDAV access to Notes directory: %s", notes_dir_path)
            notes_dir_response = self._client.request("PROPFIND", notes_dir_path, 
                                                    headers={"Depth": "0"})
            
            if notes_dir_response.status_code == 401:
                logger.error("WebDAV authentication failed for Notes directory. Please verify WebDAV permissions.")
                raise HTTPStatusError(
                    f"Authentication error accessing WebDAV Notes directory: {notes_dir_response.status_code}",
                    request=notes_dir_response.request,
                    response=notes_dir_response
                )
            elif notes_dir_response.status_code >= 400:
                logger.error("Error accessing WebDAV Notes directory: %s", notes_dir_response.status_code)
                notes_dir_response.raise_for_status()
            else:
                logger.info("Successfully accessed WebDAV Notes directory (Status: %s)", 
                           notes_dir_response.status_code)
            
            # Ensure the parent directory exists using MKCOL
            parent_dir_path = f"{webdav_base}/Notes/.attachments.{note_id}"
            logger.info("Creating attachments directory: %s", parent_dir_path)
            mkcol_response = self._client.request("MKCOL", parent_dir_path)
            # MKCOL should return 201 Created or 405 Method Not Allowed (if exists)
            # We can ignore 405, but raise for other errors
            if mkcol_response.status_code not in [201, 405]:
                logger.warning(
                    "Unexpected status code %s when creating attachments directory",
                    mkcol_response.status_code
                )
                mkcol_response.raise_for_status()
            else:
                logger.info("Created/verified directory: %s (Status: %s)", 
                           parent_dir_path, mkcol_response.status_code)

            # Proceed with the PUT request
            logger.info("Putting attachment file to: %s", attachment_path)
            response = self._client.put(
                attachment_path,
                content=content,
                headers=headers
            )
            response.raise_for_status() # Raises for 4xx/5xx status codes
            logger.info("Successfully uploaded attachment '%s' to note %s (Status: %s)", filename, note_id, response.status_code)
            # PUT typically returns 201 Created or 204 No Content on success
            return {"status_code": response.status_code} # Return status or relevant info

        except HTTPStatusError as e:
            logger.error(
                "HTTP error uploading attachment '%s' to note %s: %s",
                filename,
                note_id,
                e,
            )
            raise e
        except Exception as e:
            logger.error(
                "Unexpected error uploading attachment '%s' to note %s: %s",
                filename,
                note_id,
                e,
            )
            raise e

    def get_note_attachment(self, *, note_id: int, filename: str):
        """Fetch a specific attachment from a note via WebDAV GET."""
        webdav_base = self._get_webdav_base_path()
        attachment_path = f"{webdav_base}/Notes/.attachments.{note_id}/{filename}"
        logger.info("Fetching attachment from WebDAV path: %s", attachment_path)

        try:
            response = self._client.get(attachment_path)
            response.raise_for_status()

            content = response.content
            mime_type = response.headers.get("content-type", "application/octet-stream")

            logger.info("Successfully fetched attachment '%s' (%s, %d bytes)", filename, mime_type, len(content))
            return content, mime_type

        except HTTPStatusError as e:
            logger.error(
                "HTTP error fetching attachment '%s' for note %s: %s",
                filename,
                note_id,
                e,
            )
            raise e
        except Exception as e:
            logger.error(
                "Unexpected error fetching attachment '%s' for note %s: %s",
                filename,
                note_id,
                e,
            )
            raise e
