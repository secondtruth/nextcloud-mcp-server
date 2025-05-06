import pytest
import logging
import time
import uuid
from httpx import HTTPStatusError

from nextcloud_mcp_server.client import NextcloudClient

# Note: nc_client fixture is session-scoped in conftest.py
# Note: temporary_note and temporary_note_with_attachment fixtures are function-scoped in conftest.py

logger = logging.getLogger(__name__)

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

def test_attachments_add_and_get(nc_client: NextcloudClient, temporary_note_with_attachment: tuple):
    """
    Tests adding an attachment (via fixture) and retrieving it.
    """
    note_data, attachment_filename, attachment_content = temporary_note_with_attachment
    note_id = note_data["id"]

    logger.info(f"Attempting to retrieve attachment '{attachment_filename}' added by fixture for note ID: {note_id}")
    retrieved_content, retrieved_mime = nc_client.get_note_attachment(
        note_id=note_id,
        filename=attachment_filename
    )
    logger.info(f"Attachment retrieved. Mime type: {retrieved_mime}, Size: {len(retrieved_content)} bytes")

    assert retrieved_content == attachment_content
    assert "text/plain" in retrieved_mime # Fixture uses text/plain
    logger.info("Retrieved attachment content and mime type verified successfully.")

def test_attachments_add_to_note_with_category(nc_client: NextcloudClient, temporary_note: dict):
    """
    Tests adding and retrieving an attachment specifically for a note that has a category.
    Uses temporary_note fixture and adds attachment manually within the test.
    """
    note_data = temporary_note # Note created by fixture (has category 'TemporaryTesting')
    note_id = note_data["id"]
    note_category = note_data["category"]
    logger.info(f"Using note ID: {note_id} with category '{note_category}' for attachment test.")

    # Add attachment within the test
    unique_suffix = uuid.uuid4().hex[:8]
    attachment_filename = f"category_attach_{unique_suffix}.txt"
    attachment_content = f"Content for {attachment_filename}".encode('utf-8')
    attachment_mime = "text/plain"

    logger.info(f"Attempting to add attachment '{attachment_filename}' to note ID: {note_id}")
    upload_response = nc_client.add_note_attachment(
        note_id=note_id,
        filename=attachment_filename,
        content=attachment_content,
        mime_type=attachment_mime
    )
    assert upload_response and "status_code" in upload_response
    assert upload_response["status_code"] in [201, 204]
    logger.info(f"Attachment '{attachment_filename}' added successfully (Status: {upload_response['status_code']}).")
    time.sleep(1)

    # Get and Verify Attachment
    logger.info(f"Attempting to retrieve attachment '{attachment_filename}' from note ID: {note_id}")
    retrieved_content, retrieved_mime = nc_client.get_note_attachment(
        note_id=note_id,
        filename=attachment_filename
    )
    logger.info(f"Attachment retrieved. Mime type: {retrieved_mime}, Size: {len(retrieved_content)} bytes")

    assert retrieved_content == attachment_content
    assert attachment_mime in retrieved_mime
    logger.info("Retrieved attachment content and mime type verified successfully for note with category.")
    # Cleanup is handled by the temporary_note fixture

def test_attachments_cleanup_on_note_delete(nc_client: NextcloudClient, temporary_note_with_attachment: tuple):
    """
    Tests that the attachment (and its directory) are deleted when the parent note is deleted.
    Relies on the cleanup mechanism within notes_delete_note and the temporary_note fixture.
    """
    note_data, attachment_filename, _ = temporary_note_with_attachment
    note_id = note_data["id"]

    # Fixture setup already added the attachment.
    # Fixture teardown (from temporary_note) will delete the note.
    # We just need to verify the attachment is gone *after* the test finishes
    # and the fixture cleanup runs. However, pytest fixtures don't easily allow
    # checking state *after* cleanup.
    # Instead, we will manually delete the note here and verify the attachment is gone.

    logger.info(f"Attachment '{attachment_filename}' exists for note {note_id} (added by fixture).")

    # Manually delete the note
    logger.info(f"Manually deleting note ID: {note_id} within the test.")
    nc_client.notes_delete_note(note_id=note_id)
    logger.info(f"Note ID: {note_id} deleted successfully.")
    time.sleep(1)

    # Verify Note Is Deleted
    with pytest.raises(HTTPStatusError) as excinfo_note:
        nc_client.notes_get_note(note_id=note_id)
    assert excinfo_note.value.response.status_code == 404
    logger.info(f"Verified note {note_id} deletion (404 received).")

    # Verify Attachment Is Deleted (via 404 on GET)
    logger.info(f"Verifying attachment '{attachment_filename}' is deleted for note ID: {note_id}")
    with pytest.raises(HTTPStatusError) as excinfo_attach:
        nc_client.get_note_attachment(
            note_id=note_id,
            filename=attachment_filename
        )
    # Expect 404 because the parent directory (.attachments.NOTE_ID) should be gone
    assert excinfo_attach.value.response.status_code == 404
    logger.info(f"Attachment '{attachment_filename}' correctly not found (404) after note deletion.")

    # Note: The temporary_note fixture will still run its cleanup,
    # but it will find the note already deleted (404) and handle it gracefully.
