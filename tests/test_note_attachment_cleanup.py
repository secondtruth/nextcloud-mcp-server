import pytest
import os
import time
import logging
import uuid
from httpx import HTTPStatusError
from nextcloud_mcp_server.client import NextcloudClient

logger = logging.getLogger(__name__)

# Tests assume NEXTCLOUD_HOST, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD env vars are set

@pytest.mark.integration
def test_attachment_deleted_after_note_deletion(nc_client: NextcloudClient):
    """
    Test to verify that when a note is deleted, its attachments are also deleted
    by the MCP client's modified notes_delete_note method.
    """
    # --- Create Note ---
    unique_id = str(uuid.uuid4())
    note_title = f"Attachment Cleanup Test {unique_id}"
    note_content = f"# Test for attachment cleanup behavior\n\nThis note and its attachments should be deleted."
    note_category = "CleanupTests"

    created_note = None
    note_id = None

    try:
        # Create the note
        logger.info(f"Creating note: {note_title}")
        created_note = nc_client.notes_create_note(
            title=note_title,
            content=note_content,
            category=note_category
        )
        assert created_note and "id" in created_note
        note_id = created_note["id"]
        logger.info(f"Note created with ID: {note_id}")
        time.sleep(1)

        # Create a simple text attachment
        attachment_filename = f"cleanup_test_{unique_id}.txt"
        attachment_content = f"This is a test attachment for note {note_id}".encode('utf-8')

        # Attach the file to the note
        logger.info(f"Attaching text file to note {note_id}...")
        upload_response = nc_client.add_note_attachment(
            note_id=note_id,
            filename=attachment_filename,
            content=attachment_content,
            mime_type="text/plain"
        )

        assert upload_response["status_code"] in [201, 204]
        logger.info(f"Attachment added successfully (Status: {upload_response['status_code']}).")
        time.sleep(1)

        # Verify the attachment exists before deletion
        logger.info(f"Verifying attachment exists before deletion...")
        content, mime_type = nc_client.get_note_attachment(
            note_id=note_id,
            filename=attachment_filename
        )
        assert content == attachment_content, "Attachment content mismatch before deletion"
        logger.info("Attachment verified before deletion")

        # Now delete the note (which should also delete the attachment directory)
        logger.info(f"Deleting note ID: {note_id}")
        nc_client.notes_delete_note(note_id=note_id)
        logger.info(f"Note deleted successfully.")
        time.sleep(1)

        # Verify the note is deleted
        with pytest.raises(HTTPStatusError) as excinfo:
            nc_client.notes_get_note(note_id=note_id)
        assert excinfo.value.response.status_code == 404
        logger.info(f"Verified note deletion (404 Not Found)")

        # Now check if the attachment is deleted (expected behavior: it should be)
        logger.info(f"Checking if attachment is deleted after note deletion...")
        with pytest.raises(HTTPStatusError) as excinfo:
            nc_client.get_note_attachment(
                note_id=note_id,
                filename=attachment_filename
            )
        # We expect a 404 because the attachment (and its directory) should be gone
        assert excinfo.value.response.status_code == 404
        logger.info("CONFIRMED: Attachment is deleted after note deletion (404 Not Found)")

    finally:
        # No cleanup needed as the test itself cleans up the note and attachment
        pass
