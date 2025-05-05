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
