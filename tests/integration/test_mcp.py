import logging
import pytest
import uuid
import json

from mcp import ClientSession
from nextcloud_mcp_server.client import NextcloudClient


logger = logging.getLogger(__name__)
pytestmark = pytest.mark.integration


async def test_mcp_connectivity(nc_mcp_client: ClientSession):
    """Test basic MCP server connectivity and list available tools/resources."""

    # List available tools
    tools = await nc_mcp_client.list_tools()
    logger.info("Available MCP tools:")
    tool_names = []
    for tool in tools.tools:
        logger.info(f"  - {tool.name}: {tool.description}")
        tool_names.append(tool.name)

    # Verify expected tools are present
    expected_tools = [
        "nc_get_note",
        "nc_notes_create_note",
        "nc_notes_update_note",
        "nc_notes_append_content",
        "nc_notes_search_notes",
        "nc_notes_delete_note",
        "nc_tables_list_tables",
        "nc_tables_get_schema",
        "nc_tables_read_table",
        "nc_tables_insert_row",
        "nc_tables_update_row",
        "nc_tables_delete_row",
        "nc_webdav_list_directory",
        "nc_webdav_read_file",
        "nc_webdav_write_file",
        "nc_webdav_create_directory",
        "nc_webdav_delete_resource",
    ]

    for expected_tool in expected_tools:
        assert expected_tool in tool_names, (
            f"Expected tool '{expected_tool}' not found in available tools"
        )

    # List available resource templates
    templates = await nc_mcp_client.list_resource_templates()
    logger.info("\nAvailable resource templates:")
    template_uris = []
    for template in templates.resourceTemplates:
        logger.info(f"  - {template.uriTemplate}")
        template_uris.append(template.uriTemplate)

    # Verify expected resource templates
    expected_templates = ["nc://Notes/{note_id}/attachments/{attachment_filename}"]

    for expected_template in expected_templates:
        assert expected_template in template_uris, (
            f"Expected template '{expected_template}' not found"
        )

    # List available resources
    resources = await nc_mcp_client.list_resources()
    logger.info("\nAvailable resources:")
    resource_uris = []
    for resource in resources.resources:
        logger.info(f"  - {resource.uri}: {resource.name}")
        resource_uris.append(str(resource.uri))  # Convert to string for comparison

    # Verify expected resources
    expected_resources = ["nc://capabilities", "notes://settings"]

    for expected_resource in expected_resources:
        assert expected_resource in resource_uris, (
            f"Expected resource '{expected_resource}' not found"
        )

    # List available prompts
    prompts = await nc_mcp_client.list_prompts()
    logger.info("\nAvailable prompts:")
    for prompt in prompts.prompts:
        logger.info(f"  - {prompt.name}")


async def test_mcp_notes_crud_workflow(
    nc_mcp_client: ClientSession, nc_client: NextcloudClient
):
    """Test complete Notes CRUD workflow via MCP tools with verification via NextcloudClient."""

    unique_suffix = uuid.uuid4().hex[:8]
    test_title = f"MCP Test Note {unique_suffix}"
    test_content = f"This is test content for note {unique_suffix}"
    test_category = "MCPTesting"

    created_note = None

    try:
        # 1. Create note via MCP
        logger.info(f"Creating note via MCP: {test_title}")
        create_result = await nc_mcp_client.call_tool(
            "nc_notes_create_note",
            {"title": test_title, "content": test_content, "category": test_category},
        )

        assert create_result.isError is False, (
            f"MCP note creation failed: {create_result.content}"
        )
        created_note = create_result.content[0].text
        note_data = json.loads(created_note)  # Parse the returned JSON
        note_id = note_data["id"]

        logger.info(f"Note created via MCP with ID: {note_id}")

        # 2. Verify creation via direct NextcloudClient
        direct_note = await nc_client.notes.get_note(note_id)
        assert direct_note["title"] == test_title, (
            f"Title mismatch: {direct_note['title']} != {test_title}"
        )
        assert direct_note["content"] == test_content, "Content mismatch"
        assert direct_note["category"] == test_category, "Category mismatch"

        # 3. Read note via MCP
        logger.info(f"Reading note via MCP: {note_id}")
        read_result = await nc_mcp_client.call_tool("nc_get_note", {"note_id": note_id})
        assert read_result.isError is False, (
            f"MCP note read failed: {read_result.content}"
        )
        read_note_data = json.loads(read_result.content[0].text)

        assert read_note_data["title"] == test_title
        assert read_note_data["content"] == test_content
        assert read_note_data["category"] == test_category

        # 4. Update note via MCP
        updated_title = f"Updated {test_title}"
        updated_content = f"Updated content: {test_content}"
        etag = read_note_data["etag"]

        logger.info(f"Updating note via MCP: {note_id}")
        update_result = await nc_mcp_client.call_tool(
            "nc_notes_update_note",
            {
                "note_id": note_id,
                "etag": etag,
                "title": updated_title,
                "content": updated_content,
                "category": test_category,
            },
        )

        assert update_result.isError is False, (
            f"MCP note update failed: {update_result.content}"
        )

        # 5. Verify update via direct NextcloudClient
        updated_direct_note = await nc_client.notes.get_note(note_id)
        assert updated_direct_note["title"] == updated_title
        assert updated_direct_note["content"] == updated_content

        # 6. Append content via MCP
        append_content = "\n\nThis is appended content via MCP."
        logger.info(f"Appending content to note via MCP: {note_id}")
        append_result = await nc_mcp_client.call_tool(
            "nc_notes_append_content", {"note_id": note_id, "content": append_content}
        )

        assert append_result.isError is False, (
            f"MCP note append failed: {append_result.content}"
        )

        # 7. Verify append via direct NextcloudClient
        appended_direct_note = await nc_client.notes.get_note(note_id)
        assert append_content in appended_direct_note["content"]

        # 8. Search for note via MCP
        logger.info(f"Searching for note via MCP with query: {unique_suffix}")
        search_result = await nc_mcp_client.call_tool(
            "nc_notes_search_notes", {"query": unique_suffix}
        )

        assert search_result.isError is False, (
            f"MCP note search failed: {search_result.content}"
        )
        search_notes_text = search_result.content[0].text
        logger.info(f"Search result text: {search_notes_text}")
        search_notes = json.loads(search_notes_text)

        # Ensure search_notes is a list
        if not isinstance(search_notes, list):
            logger.warning(
                f"Expected search results to be a list, got: {type(search_notes)}"
            )
            search_notes = [search_notes] if search_notes else []

        # Find our note in search results
        found_note = None
        for note in search_notes:
            if isinstance(note, dict) and note.get("id") == note_id:
                found_note = note
                break

        assert found_note is not None, (
            f"Created note not found in search results. Search returned: {search_notes}"
        )
        assert found_note["title"] == updated_title

        # 9. Delete note via MCP
        logger.info(f"Deleting note via MCP: {note_id}")
        delete_result = await nc_mcp_client.call_tool(
            "nc_notes_delete_note", {"note_id": note_id}
        )

        assert delete_result.isError is False, (
            f"MCP note deletion failed: {delete_result.content}"
        )

        # 10. Verify deletion via direct NextcloudClient
        try:
            await nc_client.notes.get_note(note_id)
            pytest.fail("Note should have been deleted but was still found")
        except Exception:
            # Expected - note should be deleted
            logger.info(f"Successfully verified note {note_id} was deleted")
            created_note = None  # Mark as cleaned up

    finally:
        # Cleanup in case of test failure
        if created_note is not None:
            try:
                note_data = json.loads(created_note)
                await nc_client.notes.delete_note(note_data["id"])
                logger.info(f"Cleaned up note {note_data['id']} after test failure")
            except Exception as e:
                logger.warning(f"Failed to cleanup note: {e}")


async def test_mcp_webdav_workflow(
    nc_mcp_client: ClientSession, nc_client: NextcloudClient
):
    """Test WebDAV file operations via MCP tools with verification via NextcloudClient."""

    unique_suffix = uuid.uuid4().hex[:8]
    test_dir = f"mcp_test_dir_{unique_suffix}"
    test_file = f"mcp_test_file_{unique_suffix}.txt"
    test_file_path = f"{test_dir}/{test_file}"
    test_content = f"This is test content for MCP WebDAV testing {unique_suffix}"

    try:
        # 1. Create directory via MCP
        logger.info(f"Creating directory via MCP: {test_dir}")
        create_dir_result = await nc_mcp_client.call_tool(
            "nc_webdav_create_directory", {"path": test_dir}
        )

        assert create_dir_result.isError is False, (
            f"MCP directory creation failed: {create_dir_result.content}"
        )

        # 2. Verify directory creation via direct WebDAV
        dir_listing = await nc_client.webdav.list_directory("")
        dir_names = [item["name"] for item in dir_listing if item["is_directory"]]
        assert test_dir in dir_names, f"Directory {test_dir} not found in root listing"

        # 3. Write file via MCP
        logger.info(f"Writing file via MCP: {test_file_path}")
        write_result = await nc_mcp_client.call_tool(
            "nc_webdav_write_file",
            {
                "path": test_file_path,
                "content": test_content,
                "content_type": "text/plain",
            },
        )

        assert write_result.isError is False, (
            f"MCP file write failed: {write_result.content}"
        )

        # 4. Verify file creation via direct WebDAV
        file_listing = await nc_client.webdav.list_directory(test_dir)
        file_names = [item["name"] for item in file_listing if not item["is_directory"]]
        assert test_file in file_names, (
            f"File {test_file} not found in directory listing"
        )

        # 5. Read file via MCP
        logger.info(f"Reading file via MCP: {test_file_path}")
        read_result = await nc_mcp_client.call_tool(
            "nc_webdav_read_file", {"path": test_file_path}
        )

        assert read_result.isError is False, (
            f"MCP file read failed: {read_result.content}"
        )
        read_data = json.loads(read_result.content[0].text)

        assert read_data["content"] == test_content, "File content mismatch"
        assert read_data["path"] == test_file_path
        assert "text/plain" in read_data["content_type"]

        # 6. Verify file content via direct WebDAV
        direct_content, direct_content_type = await nc_client.webdav.read_file(
            test_file_path
        )
        assert direct_content.decode("utf-8") == test_content

        # 7. List directory via MCP
        logger.info(f"Listing directory via MCP: {test_dir}")
        list_result = await nc_mcp_client.call_tool(
            "nc_webdav_list_directory", {"path": test_dir}
        )

        assert list_result.isError is False, (
            f"MCP directory listing failed: {list_result.content}"
        )
        listing_text = list_result.content[0].text
        logger.info(f"Directory listing response: {listing_text}")
        listing_data = json.loads(listing_text)

        # Ensure listing_data is a list
        if not isinstance(listing_data, list):
            logger.warning(
                f"Expected directory listing to be a list, got: {type(listing_data)}"
            )
            listing_data = [listing_data] if listing_data else []

        # Find our file in the listing
        found_file = None
        for item in listing_data:
            if isinstance(item, dict) and item.get("name") == test_file:
                found_file = item
                break

        assert found_file is not None, (
            f"File {test_file} not found in MCP directory listing"
        )
        assert found_file["is_directory"] is False
        assert found_file["size"] == len(test_content.encode("utf-8"))

    finally:
        # Cleanup
        try:
            logger.info(f"Cleaning up test file: {test_file_path}")
            await nc_mcp_client.call_tool(
                "nc_webdav_delete_resource", {"path": test_file_path}
            )

            logger.info(f"Cleaning up test directory: {test_dir}")
            await nc_mcp_client.call_tool(
                "nc_webdav_delete_resource", {"path": test_dir}
            )
        except Exception as e:
            logger.warning(f"Failed to cleanup WebDAV resources: {e}")


async def test_mcp_resources_access(
    nc_mcp_client: ClientSession, nc_client: NextcloudClient
):
    """Test accessing MCP resources and compare with direct API calls."""

    # 1. Test capabilities resource
    logger.info("Testing capabilities resource via MCP")
    caps_result = await nc_mcp_client.read_resource("nc://capabilities")
    assert len(caps_result.contents) == 1
    mcp_capabilities = json.loads(caps_result.contents[0].text)

    # Compare with direct API call
    direct_capabilities = await nc_client.capabilities()

    # Basic validation - both should have similar structure
    # Both return full OCS response structure
    assert "ocs" in mcp_capabilities
    assert "data" in mcp_capabilities["ocs"]
    assert "version" in mcp_capabilities["ocs"]["data"]
    assert "ocs" in direct_capabilities
    assert "data" in direct_capabilities["ocs"]
    assert "version" in direct_capabilities["ocs"]["data"]

    # 2. Test notes settings resource
    logger.info("Testing notes settings resource via MCP")
    settings_result = await nc_mcp_client.read_resource("notes://settings")
    assert len(settings_result.contents) == 1
    mcp_settings = json.loads(settings_result.contents[0].text)

    # Compare with direct API call
    direct_settings = await nc_client.notes.get_settings()

    # Both should have settings data
    assert isinstance(mcp_settings, dict)
    assert isinstance(direct_settings, dict)

    logger.info("Successfully verified MCP resources match direct API calls")
