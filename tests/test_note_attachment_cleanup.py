import pytest
import os
import time
import logging
import uuid
from httpx import HTTPStatusError
from nextcloud_mcp_server.client import NextcloudClient

logger = logging.getLogger(__name__)

# Tests assume NEXTCLOUD_HOST, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD env vars are set

@pytest.fixture(scope="module")
def nc_client() -> NextcloudClient:
    """
    Fixture to create a NextcloudClient instance for integration tests.
    """
    assert os.getenv("NEXTCLOUD_HOST"), "NEXTCLOUD_HOST env var not set"
    assert os.getenv("NEXTCLOUD_USERNAME"), "NEXTCLOUD_USERNAME env var not set"
    assert os.getenv("NEXTCLOUD_PASSWORD"), "NEXTCLOUD_PASSWORD env var not set"
    return NextcloudClient.from_env()

@pytest.mark.integration
def test_attachment_remains_after_note_deletion(nc_client: NextcloudClient):
    """
    Test to verify and document that when a note is deleted, its attachments remain
    in the system. This is the expected behavior of the Nextcloud Notes app.
    """
    # --- Create Note ---
    unique_id = str(uuid.uuid4())
    note_title = f"Attachment Cleanup Test {unique_id}"
    note_content = f"# Test for attachment cleanup behavior\n\nThis note will be deleted, but attachments should remain."
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
        attachment_filename = f"orphan_test_{unique_id}.txt"
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
        
        # Verify the attachment exists
        content, mime_type = nc_client.get_note_attachment(
            note_id=note_id,
            filename=attachment_filename
        )
        
        assert content == attachment_content, "Attachment content mismatch"
        logger.info("Attachment verified")
        
        # Now delete the note
        logger.info(f"Deleting note ID: {note_id}")
        nc_client.notes_delete_note(note_id=note_id)
        logger.info(f"Note deleted successfully.")
        time.sleep(1)
        
        # Verify the note is deleted
        with pytest.raises(HTTPStatusError) as excinfo:
            nc_client.notes_get_note(note_id=note_id)
        assert excinfo.value.response.status_code == 404
        logger.info(f"Verified note deletion (404 Not Found)")
        
        # Now check if the attachment still exists (expected behavior: it should)
        logger.info(f"Checking if attachment still exists after note deletion...")
        orphaned_content, orphaned_mime = nc_client.get_note_attachment(
            note_id=note_id,
            filename=attachment_filename
        )
        
        # If we get here without an exception, the attachment still exists
        logger.info("CONFIRMED: Attachment still exists after note deletion")
        logger.info("This is the expected behavior of the Nextcloud Notes app")
        assert orphaned_content == attachment_content, "Orphaned attachment content mismatch"
            
    finally:
        # No cleanup needed since we've already deleted the note
        pass
