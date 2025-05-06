import pytest
import os
import time
import uuid
import tempfile
from httpx import HTTPStatusError
from PIL import Image, ImageDraw
from nextcloud_mcp_server.client import NextcloudClient

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

@pytest.fixture
def test_image():
    """Generate a test image for attachment tests"""
    # Create a temporary file to store the test image
    fd, image_path = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    
    # Create a simple test image
    img = Image.new('RGB', (200, 200), color = (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (180, 180)], fill=(255, 0, 0))
    draw.text((40, 100), "Nextcloud MCP Test", fill=(255, 255, 255))
    img.save(image_path)
    
    try:
        yield image_path
    finally:
        # Clean up the temporary image file
        if os.path.exists(image_path):
            os.unlink(image_path)

@pytest.mark.integration
def test_note_with_image_attachment(nc_client: NextcloudClient, test_image):
    """
    Test creating a note with an image attachment and properly embedding it
    in the note content using Nextcloud Notes' syntax.
    """
    # --- Create Note ---
    unique_id = str(uuid.uuid4())
    note_title = f"Note with Embedded Image {unique_id}"
    note_content = "# Note with Embedded Image\n\nThis note contains an embedded image."
    note_category = "ImageTests"
    
    created_note = None
    note_id = None
    
    try:
        # Create the note
        print(f"Creating note: {note_title}")
        created_note = nc_client.notes_create_note(
            title=note_title,
            content=note_content,
            category=note_category
        )
        assert created_note and "id" in created_note
        note_id = created_note["id"]
        print(f"Note created with ID: {note_id}")
        time.sleep(1)
        
        # Read the test image
        with open(test_image, 'rb') as f:
            image_content = f.read()
        
        # Attach the image to the note
        attachment_filename = f"test_image_{unique_id}.png"
        print(f"Attaching image to note {note_id}...")
        upload_response = nc_client.add_note_attachment(
            note_id=note_id,
            filename=attachment_filename,
            content=image_content,
            mime_type="image/png"
        )
        
        assert upload_response["status_code"] in [201, 204]
        print(f"Image attached successfully (Status: {upload_response['status_code']}).")
        time.sleep(1)
        
        # Update the note content to include a reference to the attached image
        # Try embedding using Markdown image syntax
        updated_content = f"""# Note with Embedded Image

This note contains an embedded image.

## Embedded Image (Markdown Syntax)
![Test Image](.attachments.{note_id}/{attachment_filename})

## WebDAV URL 
Files path: `/Notes/.attachments.{note_id}/{attachment_filename}`
"""
        
        # Update the note content
        print("Updating note content to include image reference...")
        updated_note = nc_client.notes_update_note(
            note_id=note_id,
            etag=created_note["etag"],
            content=updated_content
        )
        
        # Retrieve the note to verify content
        retrieved_note = nc_client.notes_get_note(note_id=note_id)
        print("Retrieved note content:")
        print(retrieved_note["content"])
        
        # Verify the image attachment can be retrieved
        content, mime_type = nc_client.get_note_attachment(
            note_id=note_id,
            filename=attachment_filename
        )
        
        assert content == image_content, "Attachment content mismatch"
        assert mime_type.startswith("image/"), f"Expected image mime type, got {mime_type}"
        print("Image attachment verified")
            
    finally:
        # Cleanup
        if note_id:
            print(f"Cleaning up - deleting note ID: {note_id}")
            try:
                nc_client.notes_delete_note(note_id=note_id)
                print(f"Note {note_id} deleted")
            except Exception as e:
                print(f"Error during cleanup: {e}")
