import pytest
import os
import time
import uuid
import logging
import tempfile
from PIL import Image, ImageDraw
from io import BytesIO
from nextcloud_mcp_server.client import NextcloudClient

logger = logging.getLogger(__name__)

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
    """Generate a test image with embedded text for attachment tests"""
    # Create a temporary file to store the test image
    fd, image_path = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    
    # Create a test image with text
    img = Image.new('RGB', (300, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (280, 180)], fill=(0, 120, 212))
    draw.text((50, 90), "Nextcloud Notes Test Image", fill=(255, 255, 255))
    img.save(image_path)
    
    try:
        yield image_path
    finally:
        # Clean up the temporary image file
        if os.path.exists(image_path):
            os.unlink(image_path)

@pytest.mark.integration
def test_note_with_embedded_image(nc_client: NextcloudClient, test_image):
    """
    Test creating a note with an embedded image and verify the process works end-to-end.
    This test documents how images should be embedded in Nextcloud Notes.
    """
    # Generate a unique identifier for this test run
    unique_id = str(uuid.uuid4())[:8]
    note_title = f"Embedded Image Test {unique_id}"
    initial_content = "# Embedded Image Test\n\nThis note demonstrates how to properly embed images in Nextcloud Notes."
    
    # Create the note
    logger.info(f"Creating test note: {note_title}")
    note = nc_client.notes_create_note(
        title=note_title,
        content=initial_content,
        category="Documentation"
    )
    note_id = note["id"]
    note_etag = note["etag"]
    logger.info(f"Note created with ID: {note_id}")
    
    try:
        # Read the test image content
        with open(test_image, 'rb') as f:
            image_content = f.read()
        
        # Generate a unique filename for the attachment
        attachment_filename = f"test_image_{unique_id}.png"
        
        # Upload the image as an attachment
        logger.info(f"Uploading image attachment '{attachment_filename}' to note {note_id}...")
        upload_response = nc_client.add_note_attachment(
            note_id=note_id,
            filename=attachment_filename,
            content=image_content,
            mime_type="image/png"
        )
        logger.info(f"Image uploaded: {upload_response}")
        
        # Update the note content to include the embedded image using Markdown syntax
        # This is the correct syntax for embedding images in Nextcloud Notes
        updated_content = f"""# Embedded Image Test

This note demonstrates how to properly embed images in Nextcloud Notes.

## Method 1: Markdown Image Syntax
![Test Image](.attachments.{note_id}/{attachment_filename})

## Method 2: HTML Image Tag
<img src=".attachments.{note_id}/{attachment_filename}" alt="Test Image HTML" width="300" />

## Notes on Image Embedding
- Images must be stored in the .attachments.{note_id} directory
- Images are referenced using relative paths
- Both Markdown and HTML image tags work in Nextcloud Notes
- The Nextcloud Notes UI will display these images inline when viewing the note
"""
        
        # Update the note with the image references
        logger.info("Updating note content with image references...")
        updated_note = nc_client.notes_update_note(
            note_id=note_id,
            etag=note_etag,
            content=updated_content
        )
        
        # Verify the updated note has the correct content
        retrieved_note = nc_client.notes_get_note(note_id=note_id)
        assert ".attachments." in retrieved_note["content"], "Image reference not found in note content"
        logger.info("Note updated successfully with image references")
        
        # Verify we can retrieve the image attachment
        retrieved_content, mime_type = nc_client.get_note_attachment(
            note_id=note_id,
            filename=attachment_filename
        )
        assert len(retrieved_content) > 0, "Retrieved image content is empty"
        assert mime_type.startswith("image/"), f"Expected image mime type, got {mime_type}"
        
        logger.info("Test completed successfully - image was embedded in the note and can be retrieved")
        
    finally:
        # Clean up - delete the test note
        logger.info(f"Cleaning up - deleting test note {note_id}")
        nc_client.notes_delete_note(note_id=note_id)
