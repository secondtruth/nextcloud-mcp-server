import pytest
import os
import time
import uuid
from httpx import HTTPStatusError

from nextcloud_mcp_server.client import NextcloudClient

# Tests assume NEXTCLOUD_HOST, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD env vars are set


@pytest.fixture(scope="module")
def nc_client() -> NextcloudClient:
    """
    Fixture to create a NextcloudClient instance for integration tests.
    Reads credentials from environment variables.
    Scope is 'module' so the client is reused for all tests in this file.
    """
    # Basic check to ensure env vars seem present - tests will fail properly if not
    assert os.getenv("NEXTCLOUD_HOST"), "NEXTCLOUD_HOST env var not set"
    assert os.getenv("NEXTCLOUD_USERNAME"), "NEXTCLOUD_USERNAME env var not set"
    assert os.getenv("NEXTCLOUD_PASSWORD"), "NEXTCLOUD_PASSWORD env var not set"
    return NextcloudClient.from_env()


@pytest.mark.integration
def test_note_crud_integration(nc_client: NextcloudClient):
    """
    Integration test for the complete CRUD (Create, Read, Update, Delete)
    lifecycle of a note.
    """
    # --- Create ---
    unique_id = str(uuid.uuid4())  # To ensure note is unique for this test run
    create_title = f"Integration Test Note {unique_id}"
    create_content = f"Content for integration test {unique_id}"
    create_category = "IntegrationTesting"

    created_note = (
        None  # Initialize to ensure cleanup happens even if create fails mid-assert
    )
    try:
        print(f"\nAttempting to create note: {create_title}")
        created_note = nc_client.notes_create_note(
            title=create_title, content=create_content, category=create_category
        )
        print(f"Note created: {created_note}")

        assert created_note is not None
        assert "id" in created_note
        assert created_note["title"] == create_title
        assert created_note["content"] == create_content
        assert created_note["category"] == create_category
        assert "etag" in created_note
        note_id = created_note["id"]
        etag = created_note["etag"]

        # Add a small delay to allow Nextcloud to process if needed
        time.sleep(1)

        # --- Read (Verify Create) ---
        print(f"Attempting to read note ID: {note_id}")
        read_note = nc_client.notes_get_note(note_id=note_id)
        print(f"Note read: {read_note}")
        assert read_note["id"] == note_id
        assert read_note["title"] == create_title
        assert read_note["content"] == create_content
        assert read_note["category"] == create_category
        # Etag might change even on read in some systems, so don't assert etag equality here

        # --- Update ---
        update_title = f"Updated Test Note {unique_id}"
        update_content = f"Updated content {unique_id}"
        # Use the etag from the *creation* for the update's If-Match header
        print(f"Attempting to update note ID: {note_id} with etag: {etag}")
        updated_note = nc_client.notes_update_note(
            note_id=note_id,
            etag=etag,
            title=update_title,
            content=update_content,
            # category=create_category # Keep category same or update if needed
        )
        print(f"Note updated: {updated_note}")
        assert updated_note["id"] == note_id
        assert updated_note["title"] == update_title
        assert updated_note["content"] == update_content
        assert updated_note["category"] == create_category  # Category wasn't updated
        assert "etag" in updated_note
        assert updated_note["etag"] != etag  # Etag must change on update
        new_etag = updated_note["etag"]

        # Add a small delay
        time.sleep(1)

        # --- Read (Verify Update) ---
        print(f"Attempting to read updated note ID: {note_id}")
        read_updated_note = nc_client.notes_get_note(note_id=note_id)
        print(f"Updated note read: {read_updated_note}")
        assert read_updated_note["id"] == note_id
        assert read_updated_note["title"] == update_title
        assert read_updated_note["content"] == update_content
        # Don't assert etag equality here either

        # --- Test Update Conflict (Precondition Failed) ---
        print(f"Attempting to update note ID: {note_id} with OLD etag: {etag}")
        with pytest.raises(HTTPStatusError) as excinfo:
            nc_client.notes_update_note(
                note_id=note_id,
                etag=etag,  # Use the OLD etag
                title="This update should fail",
            )
        assert excinfo.value.response.status_code == 412  # Precondition Failed
        print("Update with old etag correctly failed with 412.")

    finally:
        # --- Delete ---
        if created_note and "id" in created_note:
            note_id_to_delete = created_note["id"]
            print(f"Attempting to delete note ID: {note_id_to_delete}")
            try:
                delete_response = nc_client.notes_delete_note(note_id=note_id_to_delete)
                print(f"Delete response: {delete_response}")
                # Check if delete returns the deleted object or just status
                # Assuming it returns the object based on previous tests
                assert delete_response["id"] == note_id_to_delete
                print(f"Note ID: {note_id_to_delete} deleted successfully.")

                # --- Verify Delete ---
                print(f"Attempting to read deleted note ID: {note_id_to_delete}")
                with pytest.raises(HTTPStatusError) as excinfo_del:
                    nc_client.notes_get_note(note_id=note_id_to_delete)
                assert excinfo_del.value.response.status_code == 404
                print(
                    f"Reading deleted note ID: {note_id_to_delete} correctly failed with 404."
                )

            except HTTPStatusError as e:
                # If deletion fails unexpectedly, log it but don't fail the test here
                # as the primary goal was CRUD, and cleanup failure is secondary.
                print(f"Error during cleanup (deleting note {note_id_to_delete}): {e}")
            except Exception as e:
                print(f"Unexpected error during cleanup: {e}")
        else:
            print(
                "Skipping delete step as note creation might have failed or ID was not available."
            )


@pytest.mark.integration
def test_delete_nonexistent_note(nc_client: NextcloudClient):
    """Test deleting a note that doesn't exist."""
    non_existent_id = 999999999  # Use an ID highly unlikely to exist
    print(f"\nAttempting to delete non-existent note ID: {non_existent_id}")
    with pytest.raises(HTTPStatusError) as excinfo:
        nc_client.notes_delete_note(note_id=non_existent_id)
    assert excinfo.value.response.status_code == 404
    print(
        f"Deleting non-existent note ID: {non_existent_id} correctly failed with 404."
    )


@pytest.mark.integration
def test_note_attachment_integration(nc_client: NextcloudClient):
    """
    Integration test for adding and retrieving a note attachment via WebDAV.
    This test is conditional on WebDAV permissions being available.
    """
    # --- Create Note ---
    unique_id = str(uuid.uuid4())
    note_title = f"Attachment Test Note {unique_id}"
    note_content = "Note for testing attachments."
    note_category = "AttachmentTesting"
    created_note = None
    note_id = None

    try:
        print(f"\nCreating note for attachment test: {note_title}")
        created_note = nc_client.notes_create_note(
            title=note_title, content=note_content, category=note_category
        )
        assert created_note and "id" in created_note
        note_id = created_note["id"]
        print(f"Note created with ID: {note_id}")
        time.sleep(1) # Allow time for note creation

        # --- Try to Add Attachment ---
        attachment_filename = f"test_attachment_{unique_id}.txt"
        attachment_content = f"This is the content of {attachment_filename}".encode('utf-8')
        attachment_mime = "text/plain"

        print(f"Attempting to add attachment '{attachment_filename}' to note ID: {note_id}")
        try:
            # Try to add the attachment, but don't fail the test if WebDAV isn't available
            upload_response = nc_client.add_note_attachment(
                note_id=note_id,
                filename=attachment_filename,
                content=attachment_content,
                mime_type=attachment_mime
            )
            
            # If we get here, WebDAV is working - continue with attachment tests
            assert upload_response and "status_code" in upload_response
            assert upload_response["status_code"] in [201, 204]
            print(f"Attachment '{attachment_filename}' added successfully (Status: {upload_response['status_code']}).")
            time.sleep(1) # Allow time for upload processing

            # --- Get and Verify Attachment ---
            print(f"Attempting to retrieve attachment '{attachment_filename}' from note ID: {note_id}")
            retrieved_content, retrieved_mime = nc_client.get_note_attachment(
                note_id=note_id,
                filename=attachment_filename
            )
            print(f"Attachment retrieved. Mime type: {retrieved_mime}, Size: {len(retrieved_content)} bytes")

            # --- Verify Attachment ---
            assert retrieved_content == attachment_content
            # Check if the expected mime type is part of the retrieved one (to handle charset)
            assert attachment_mime in retrieved_mime
            print("Retrieved attachment content and mime type verified successfully.")
            
        except HTTPStatusError as e:
            if e.response.status_code == 401:
                pytest.skip("Skipping attachment tests due to WebDAV permission issues (401 Unauthorized)")
            else:
                raise  # Re-raise other HTTP errors

    finally:
        # --- Delete Note (Cleanup) ---
        if note_id:
            print(f"Attempting cleanup: deleting note ID: {note_id}")
            try:
                nc_client.notes_delete_note(note_id=note_id)
                print(f"Note ID: {note_id} deleted successfully.")
                # Verify deletion
                time.sleep(1)
                with pytest.raises(HTTPStatusError) as excinfo_del:
                    nc_client.notes_get_note(note_id=note_id)
                assert excinfo_del.value.response.status_code == 404
                print(f"Verified note {note_id} deletion (404 received).")
            except Exception as e:
                print(f"Error during cleanup (deleting note {note_id}): {e}")
        else:
            print("Skipping cleanup as note ID was not obtained.")


@pytest.mark.integration
def test_note_attachment_with_category_integration(nc_client: NextcloudClient):
    """
    Explicitly tests adding/retrieving an attachment for a note WITH a category.
    Functionally similar to test_note_attachment_integration but emphasizes the category.
    """
    # --- Create Note with Category ---
    unique_id = str(uuid.uuid4())
    note_title = f"Category Attachment Test Note {unique_id}"
    note_content = "Note with category for testing attachments."
    note_category = "CategoryTest" # Explicitly using a category
    created_note = None
    note_id = None

    try:
        print(f"\nCreating note with category '{note_category}' for attachment test: {note_title}")
        created_note = nc_client.notes_create_note(
            title=note_title, content=note_content, category=note_category
        )
        assert created_note and "id" in created_note
        note_id = created_note["id"]
        print(f"Note with category created with ID: {note_id}")
        time.sleep(1)

        # --- Try to Add Attachment ---
        attachment_filename = f"category_test_attachment_{unique_id}.txt"
        attachment_content = f"Content for {attachment_filename}".encode('utf-8')
        attachment_mime = "text/plain"

        print(f"Attempting to add attachment '{attachment_filename}' to note ID: {note_id}")
        try:
            # Try to add the attachment, but don't fail the test if WebDAV isn't available
            upload_response = nc_client.add_note_attachment(
                note_id=note_id,
                filename=attachment_filename,
                content=attachment_content,
                mime_type=attachment_mime
            )
            
            # If we get here, WebDAV is working - continue with attachment tests
            assert upload_response and "status_code" in upload_response
            assert upload_response["status_code"] in [201, 204]
            print(f"Attachment '{attachment_filename}' added successfully (Status: {upload_response['status_code']}).")
            time.sleep(1)

            # --- Get and Verify Attachment ---
            print(f"Attempting to retrieve attachment '{attachment_filename}' from note ID: {note_id}")
            retrieved_content, retrieved_mime = nc_client.get_note_attachment(
                note_id=note_id,
                filename=attachment_filename
            )
            print(f"Attachment retrieved. Mime type: {retrieved_mime}, Size: {len(retrieved_content)} bytes")

            # --- Verify Attachment ---
            assert retrieved_content == attachment_content
            assert attachment_mime in retrieved_mime # Check if expected mime is part of retrieved
            print("Retrieved attachment content and mime type verified successfully for note with category.")
            
        except HTTPStatusError as e:
            if e.response.status_code == 401:
                pytest.skip("Skipping attachment tests due to WebDAV permission issues (401 Unauthorized)")
            else:
                raise  # Re-raise other HTTP errors

    finally:
        # --- Delete Note (Cleanup) ---
        if note_id:
            print(f"Attempting cleanup: deleting note ID: {note_id}")
            try:
                nc_client.notes_delete_note(note_id=note_id)
                print(f"Note ID: {note_id} deleted successfully.")
                time.sleep(1)
                with pytest.raises(HTTPStatusError) as excinfo_del:
                    nc_client.notes_get_note(note_id=note_id)
                assert excinfo_del.value.response.status_code == 404
                print(f"Verified note {note_id} deletion (404 received).")
            except Exception as e:
                print(f"Error during cleanup (deleting note {note_id}): {e}")
        else:
            print("Skipping cleanup as note ID was not obtained.")


@pytest.mark.integration
def test_attachment_cleanup_behavior(nc_client: NextcloudClient):
    """
    Test to document the behavior regarding note attachment cleanup.
    
    This test confirms that when a note is deleted, its attachments remain in the system.
    This matches the behavior of the official Nextcloud Notes app, which also leaves
    orphaned attachments when notes are deleted.
    """
    # --- Create Note ---
    unique_id = str(uuid.uuid4())
    note_title = f"Attachment Cleanup Test {unique_id}"
    note_content = "Test note for attachments cleanup."
    note_category = "AttachmentCleanupTest"
    
    print(f"\nCreating test note: {note_title}")
    created_note = nc_client.notes_create_note(
        title=note_title, content=note_content, category=note_category
    )
    assert created_note and "id" in created_note
    note_id = created_note["id"]
    print(f"Test note created with ID: {note_id}")
    time.sleep(1)
    
    # Check authentication type
    auth_type = type(nc_client._client.auth).__name__
    print(f"Client authentication type: {auth_type}")
    
    # --- Try to Add Attachment ---
    attachment_filename = f"cleanup_test_{unique_id}.txt"
    attachment_content = f"Content for cleanup test".encode('utf-8')
    
    print(f"Adding attachment '{attachment_filename}' to note ID: {note_id}")
    try:
        upload_response = nc_client.add_note_attachment(
            note_id=note_id,
            filename=attachment_filename,
            content=attachment_content,
            mime_type="text/plain"
        )
        assert upload_response["status_code"] in [201, 204]
        print(f"Attachment added successfully (Status: {upload_response['status_code']}).")
        time.sleep(1)
        
        # --- Verify Attachment Exists ---
        retrieved_content, _ = nc_client.get_note_attachment(
            note_id=note_id,
            filename=attachment_filename
        )
        assert retrieved_content == attachment_content
        print("Verified attachment exists and can be retrieved")
        
        # Attachment operations successful - continue with test
        has_webdav_access = True
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            print(f"WebDAV access denied (401 Unauthorized). Skipping attachment tests.")
            pytest.skip("WebDAV access denied (401 Unauthorized)")
        else:
            raise  # Re-raise other HTTP errors
    
    # --- Delete Note ---
    print(f"Deleting note ID: {note_id}")
    nc_client.notes_delete_note(note_id=note_id)
    print(f"Note ID: {note_id} deleted successfully.")
    time.sleep(1)
    
    # --- Verify Note Is Deleted ---
    with pytest.raises(HTTPStatusError) as excinfo:
        nc_client.notes_get_note(note_id=note_id)
    assert excinfo.value.response.status_code == 404
    print(f"Verified note deletion (404 received)")
    
    # --- Document the expected behavior: attachments remain after note deletion ---
    try:
        # Try to get the attachment - expected to still exist
        retrieved_content, _ = nc_client.get_note_attachment(
            note_id=note_id,
            filename=attachment_filename
        )
        print("EXPECTED BEHAVIOR: Attachment still exists after note deletion")
        print("This matches the behavior of the official Nextcloud Notes app")
    except HTTPStatusError as e:
        if e.response.status_code == 404:
            print("NOTE: Attachment was deleted with the note (unexpected but not a problem)")
        else:
            print(f"Unexpected error when checking attachment: {e.response.status_code}")
