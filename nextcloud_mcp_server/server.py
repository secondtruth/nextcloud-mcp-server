# server.py
import logging
from typing import Optional
from datetime import datetime, timedelta
from nextcloud_mcp_server.config import setup_logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP, Context
from collections.abc import AsyncIterator
from nextcloud_mcp_server.client import NextcloudClient

setup_logging()


@dataclass
class AppContext:
    client: NextcloudClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    logging.info("Creating Nextcloud client")
    client = NextcloudClient.from_env()
    logging.info("Client initialization wait complete.")
    try:
        yield AppContext(client=client)
    finally:
        # Cleanup on shutdown
        await client.close()


# Create an MCP server
mcp = FastMCP("Nextcloud MCP", lifespan=app_lifespan)

logger = logging.getLogger(__name__)


@mcp.resource("nc://capabilities")
async def nc_get_capabilities():
    """Get the Nextcloud Host capabilities"""
    ctx: Context = (
        mcp.get_context()
    )  # https://github.com/modelcontextprotocol/python-sdk/issues/244
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.capabilities()


@mcp.resource("notes://settings")
async def notes_get_settings():
    """Get the Notes App settings"""
    ctx: Context = (
        mcp.get_context()
    )  # https://github.com/modelcontextprotocol/python-sdk/issues/244
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.notes.get_settings()


@mcp.tool()
async def nc_get_note(note_id: int, ctx: Context):
    """Get user note using note id"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.notes.get_note(note_id)


@mcp.tool()
async def nc_notes_create_note(title: str, content: str, category: str, ctx: Context):
    """Create a new note"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.notes.create_note(
        title=title,
        content=content,
        category=category,
    )


@mcp.tool()
async def nc_notes_update_note(
    note_id: int,
    etag: str,
    title: str | None,
    content: str | None,
    category: str | None,
    ctx: Context,
):
    logger.info("Updating note %s", note_id)
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.notes.update(
        note_id=note_id,
        etag=etag,
        title=title,
        content=content,
        category=category,
    )


@mcp.tool()
async def nc_notes_append_content(note_id: int, content: str, ctx: Context):
    """Append content to an existing note with a clear separator"""
    logger.info("Appending content to note %s", note_id)
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.notes.append_content(note_id=note_id, content=content)


@mcp.tool()
async def nc_notes_search_notes(query: str, ctx: Context):
    """Search notes by title or content, returning only id, title, and category."""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.notes_search_notes(query=query)


@mcp.tool()
async def nc_notes_delete_note(note_id: int, ctx: Context):
    logger.info("Deleting note %s", note_id)
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.notes.delete_note(note_id)


# Tables tools
@mcp.tool()
async def nc_tables_list_tables(ctx: Context):
    """List all tables available to the user"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.tables.list_tables()


@mcp.tool()
async def nc_tables_get_schema(table_id: int, ctx: Context):
    """Get the schema/structure of a specific table including columns and views"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.tables.get_table_schema(table_id)


@mcp.tool()
async def nc_tables_read_table(
    table_id: int,
    ctx: Context,
    limit: int | None = None,
    offset: int | None = None,
):
    """Read rows from a table with optional pagination"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.tables.get_table_rows(table_id, limit, offset)


@mcp.tool()
async def nc_tables_insert_row(table_id: int, data: dict, ctx: Context):
    """Insert a new row into a table.

    Data should be a dictionary mapping column IDs to values, e.g. {1: "text", 2: 42}
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.tables.create_row(table_id, data)


@mcp.tool()
async def nc_tables_update_row(row_id: int, data: dict, ctx: Context):
    """Update an existing row in a table.

    Data should be a dictionary mapping column IDs to new values, e.g. {1: "new text", 2: 99}
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.tables.update_row(row_id, data)


@mcp.tool()
async def nc_tables_delete_row(row_id: int, ctx: Context):
    """Delete a row from a table"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.tables.delete_row(row_id)


@mcp.resource("nc://Notes/{note_id}/attachments/{attachment_filename}")
async def nc_notes_get_attachment(note_id: int, attachment_filename: str):
    """Get a specific attachment from a note"""
    ctx: Context = mcp.get_context()
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    # Assuming a method get_note_attachment exists in the client
    # This method should return the raw content and determine the mime type
    content, mime_type = await client.webdav.get_note_attachment(
        note_id=note_id, filename=attachment_filename
    )
    return {
        "contents": [
            {
                # Use uppercase 'Notes' to match the decorator
                "uri": f"nc://Notes/{note_id}/attachments/{attachment_filename}",
                "mimeType": mime_type,  # Client needs to determine this
                "data": content,  # Return raw bytes/data
            }
        ]
    }


# WebDAV file system tools
@mcp.tool()
async def nc_webdav_list_directory(ctx: Context, path: str = ""):
    """List files and directories in the specified NextCloud path.

    Args:
        path: Directory path to list (empty string for root directory)

    Returns:
        List of items with metadata including name, path, is_directory, size, content_type, last_modified

    Examples:
        # List root directory
        await nc_webdav_list_directory("")

        # List a specific folder
        await nc_webdav_list_directory("Documents/Projects")
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.webdav.list_directory(path)


@mcp.tool()
async def nc_webdav_read_file(path: str, ctx: Context):
    """Read the content of a file from NextCloud.

    Args:
        path: Full path to the file to read

    Returns:
        Dict with path, content, content_type, size, and encoding (if binary)
        Text files are decoded to UTF-8, binary files are base64 encoded

    Examples:
        # Read a text file
        result = await nc_webdav_read_file("Documents/readme.txt")
        print(result['content'])  # Decoded text content

        # Read a binary file
        result = await nc_webdav_read_file("Images/photo.jpg")
        print(result['encoding'])  # 'base64'
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    content, content_type = await client.webdav.read_file(path)

    # For text files, decode content for easier viewing
    if content_type and content_type.startswith("text/"):
        try:
            decoded_content = content.decode("utf-8")
            return {
                "path": path,
                "content": decoded_content,
                "content_type": content_type,
                "size": len(content),
            }
        except UnicodeDecodeError:
            pass

    # For binary files, return metadata and base64 encoded content
    import base64

    return {
        "path": path,
        "content": base64.b64encode(content).decode("ascii"),
        "content_type": content_type,
        "size": len(content),
        "encoding": "base64",
    }


@mcp.tool()
async def nc_webdav_write_file(
    path: str, content: str, ctx: Context, content_type: str | None = None
):
    """Write content to a file in NextCloud.

    Args:
        path: Full path where to write the file
        content: File content (text or base64 for binary)
        content_type: MIME type (auto-detected if not provided, use 'type;base64' for binary)

    Returns:
        Dict with status_code indicating success

    Examples:
        # Write a text file
        await nc_webdav_write_file("Documents/notes.md", "# My Notes\nContent here...")

        # Write binary data (base64 encoded)
        await nc_webdav_write_file("files/data.bin", base64_content, "application/octet-stream;base64")
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client

    # Handle base64 encoded content
    if content_type and "base64" in content_type.lower():
        import base64

        content_bytes = base64.b64decode(content)
        content_type = content_type.replace(";base64", "")
    else:
        content_bytes = content.encode("utf-8")

    return await client.webdav.write_file(path, content_bytes, content_type)


@mcp.tool()
async def nc_webdav_create_directory(path: str, ctx: Context):
    """Create a directory in NextCloud.

    Args:
        path: Full path of the directory to create

    Returns:
        Dict with status_code (201 for created, 405 if already exists)

    Examples:
        # Create a single directory
        await nc_webdav_create_directory("NewProject")

        # Create nested directories (parent must exist)
        await nc_webdav_create_directory("Projects/MyApp/docs")
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.webdav.create_directory(path)


@mcp.tool()
async def nc_webdav_delete_resource(path: str, ctx: Context):
    """Delete a file or directory in NextCloud.

    Args:
        path: Full path of the file or directory to delete

    Returns:
        Dict with status_code indicating result (404 if not found)

    Examples:
        # Delete a file
        await nc_webdav_delete_resource("old_document.txt")

        # Delete a directory (will delete all contents)
        await nc_webdav_delete_resource("temp_folder")
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.webdav.delete_resource(path)


# Calendar tools
@mcp.tool()
async def nc_calendar_list_calendars(ctx: Context):
    """List all available calendars for the user"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.calendar.list_calendars()


@mcp.tool()
async def nc_calendar_create_event(
    calendar_name: str,
    title: str,
    start_datetime: str,
    ctx: Context,
    end_datetime: str = "",
    all_day: bool = False,
    description: str = "",
    location: str = "",
    categories: str = "",
    recurring: bool = False,
    recurrence_rule: str = "",
    recurrence_end_date: str = "",
    reminder_minutes: int = 15,
    reminder_email: bool = False,
    status: str = "CONFIRMED",
    priority: int = 5,
    privacy: str = "PUBLIC",
    attendees: str = "",
    url: str = "",
    color: str = "",
):
    """Create a comprehensive calendar event with full feature support

    Args:
        calendar_name: Name of the calendar to create the event in
        title: Event title
        start_datetime: ISO format: "2025-01-15T14:00:00" or "2025-01-15" for all-day
        ctx: MCP context
        end_datetime: ISO format end time, empty for all-day events
        all_day: Whether this is an all-day event
        description: Event description/details
        location: Event location
        categories: Comma-separated categories (e.g., "work,meeting")
        recurring: Whether this is a recurring event
        recurrence_rule: RFC5545 RRULE (e.g., "FREQ=WEEKLY;BYDAY=MO,WE,FR")
        recurrence_end_date: When to stop recurring
        reminder_minutes: Minutes before event to send reminder
        reminder_email: Whether to send email notification
        status: Event status: CONFIRMED, TENTATIVE, or CANCELLED
        priority: Priority level 1-9 (1=highest, 9=lowest, 5=normal)
        privacy: Privacy level: PUBLIC, PRIVATE, or CONFIDENTIAL
        attendees: Comma-separated email addresses
        url: Related URL for the event
        color: Event color (hex or name)

    Returns:
        Dict with event creation result
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client

    event_data = {
        "title": title,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "all_day": all_day,
        "description": description,
        "location": location,
        "categories": categories,
        "recurring": recurring,
        "recurrence_rule": recurrence_rule,
        "recurrence_end_date": recurrence_end_date,
        "reminder_minutes": reminder_minutes,
        "reminder_email": reminder_email,
        "status": status,
        "priority": priority,
        "privacy": privacy,
        "attendees": attendees,
        "url": url,
        "color": color,
    }

    return await client.calendar.create_event(calendar_name, event_data)


@mcp.tool()
async def nc_calendar_list_events(
    calendar_name: str,
    ctx: Context,
    start_date: str = "",
    end_date: str = "",
    limit: int = 50,
    min_attendees: Optional[int] = None,
    min_duration_minutes: Optional[int] = None,
    categories: Optional[str] = None,
    status: Optional[str] = None,
    title_contains: Optional[str] = None,
    location_contains: Optional[str] = None,
    search_all_calendars: bool = False,
):
    """List events in a calendar (or all calendars) within date range with advanced filtering.

    Args:
        calendar_name: Name of the calendar to search. Ignored if search_all_calendars=True.
        ctx: MCP context
        start_date: Start date for search (YYYY-MM-DD format, e.g., "2025-01-01")
        end_date: End date for search (YYYY-MM-DD format, e.g., "2025-01-31")
        limit: Maximum number of events to return
        min_attendees: Filter events with at least this many attendees
        min_duration_minutes: Filter events with at least this duration
        categories: Filter events containing any of these categories (comma-separated, e.g., "work,meeting")
        status: Filter events by status (CONFIRMED, TENTATIVE, or CANCELLED)
        title_contains: Filter events where title contains this text
        location_contains: Filter events where location contains this text
        search_all_calendars: If True, search across all calendars instead of just one

    Returns:
        List of events matching the filters
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client

    # Build filters dictionary
    filters = {}
    if min_attendees is not None:
        filters["min_attendees"] = min_attendees
    if min_duration_minutes is not None:
        filters["min_duration_minutes"] = min_duration_minutes
    if categories is not None:
        filters["categories"] = [cat.strip() for cat in categories.split(",")]
    if status is not None:
        filters["status"] = status
    if title_contains is not None:
        filters["title_contains"] = title_contains
    if location_contains is not None:
        filters["location_contains"] = location_contains

    if search_all_calendars:
        # Search across all calendars with filters
        events = await client.calendar.search_events_across_calendars(
            start_date=start_date,
            end_date=end_date,
            filters=filters if filters else None,
        )
        return events[:limit]
    else:
        # Search in specific calendar
        events = await client.calendar.get_calendar_events(
            calendar_name=calendar_name,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        # Apply filters if provided
        if filters:
            events = client.calendar._apply_event_filters(events, filters)

        return events


@mcp.tool()
async def nc_calendar_get_event(
    calendar_name: str,
    event_uid: str,
    ctx: Context,
):
    """Get detailed information about a specific event"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    event_data, etag = await client.calendar.get_event(calendar_name, event_uid)
    return event_data


@mcp.tool()
async def nc_calendar_update_event(
    calendar_name: str,
    event_uid: str,
    ctx: Context,
    # All the same parameters as create_event but optional
    title: str | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    all_day: bool | None = None,
    description: str | None = None,
    location: str | None = None,
    categories: str | None = None,
    # Recurrence updates
    recurring: bool | None = None,
    recurrence_rule: str | None = None,
    # Notification updates
    reminder_minutes: int | None = None,
    reminder_email: bool | None = None,
    # Event property updates
    status: str | None = None,
    priority: int | None = None,
    privacy: str | None = None,
    attendees: str | None = None,
    url: str | None = None,
    color: str | None = None,
    etag: str = "",
):
    """Update any aspect of an existing event"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client

    # Build update data with only non-None values
    event_data = {}
    if title is not None:
        event_data["title"] = title
    if start_datetime is not None:
        event_data["start_datetime"] = start_datetime
    if end_datetime is not None:
        event_data["end_datetime"] = end_datetime
    if all_day is not None:
        event_data["all_day"] = all_day
    if description is not None:
        event_data["description"] = description
    if location is not None:
        event_data["location"] = location
    if categories is not None:
        event_data["categories"] = categories
    if recurring is not None:
        event_data["recurring"] = recurring
    if recurrence_rule is not None:
        event_data["recurrence_rule"] = recurrence_rule
    if reminder_minutes is not None:
        event_data["reminder_minutes"] = reminder_minutes
    if reminder_email is not None:
        event_data["reminder_email"] = reminder_email
    if status is not None:
        event_data["status"] = status
    if priority is not None:
        event_data["priority"] = priority
    if privacy is not None:
        event_data["privacy"] = privacy
    if attendees is not None:
        event_data["attendees"] = attendees
    if url is not None:
        event_data["url"] = url
    if color is not None:
        event_data["color"] = color

    return await client.calendar.update_event(
        calendar_name, event_uid, event_data, etag
    )


@mcp.tool()
async def nc_calendar_delete_event(
    calendar_name: str,
    event_uid: str,
    ctx: Context,
):
    """Delete a calendar event"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client
    return await client.calendar.delete_event(calendar_name, event_uid)


@mcp.tool()
async def nc_calendar_create_meeting(
    title: str,
    date: str,
    time: str,
    ctx: Context,
    duration_minutes: int = 60,
    calendar_name: str = "personal",
    attendees: str = "",
    location: str = "",
    description: str = "",
    reminder_minutes: int = 15,
):
    """Quick meeting creation with smart defaults

    This is a convenience function for creating events with common meeting defaults.
    It automatically:
    - Calculates end time based on duration
    - Sets status to CONFIRMED
    - Adds a reminder
    - Uses simpler date/time inputs instead of full ISO format

    For full control over all event properties, use nc_calendar_create_event instead.

    Args:
        title: Meeting title
        date: Meeting date (YYYY-MM-DD format, e.g., "2025-01-15")
        time: Meeting start time (HH:MM format, e.g., "14:00")
        ctx: MCP context
        duration_minutes: Meeting duration in minutes (default: 60)
        calendar_name: Calendar to create the meeting in (default: "personal")
        attendees: Comma-separated email addresses of attendees
        location: Meeting location
        description: Meeting description/agenda
        reminder_minutes: Minutes before meeting to send reminder (default: 15)

    Returns:
        Dict with meeting creation result
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client

    # Combine date and time for start_datetime
    start_datetime = f"{date}T{time}:00"

    # Calculate end_datetime

    start_dt = datetime.fromisoformat(start_datetime)
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    end_datetime = end_dt.isoformat()

    event_data = {
        "title": title,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "all_day": False,
        "description": description,
        "location": location,
        "attendees": attendees,
        "reminder_minutes": reminder_minutes,
        "status": "CONFIRMED",
        "priority": 5,
        "privacy": "PUBLIC",
    }

    return await client.calendar.create_event(calendar_name, event_data)


@mcp.tool()
async def nc_calendar_get_upcoming_events(
    ctx: Context,
    calendar_name: str = "",  # Empty = all calendars
    days_ahead: int = 7,
    limit: int = 10,
):
    """Get upcoming events in next N days"""
    client: NextcloudClient = ctx.request_context.lifespan_context.client

    now = datetime.now()
    end_date = now + timedelta(days=days_ahead)

    start_date_str = now.strftime("%Y%m%dT%H%M%SZ")
    end_date_str = end_date.strftime("%Y%m%dT%H%M%SZ")

    if calendar_name:
        # Get events from specific calendar
        return await client.calendar.get_calendar_events(
            calendar_name=calendar_name,
            start_date=start_date_str,
            end_date=end_date_str,
            limit=limit,
        )
    else:
        # Get events from all calendars
        all_calendars = await client.calendar.list_calendars()
        all_events = []

        for calendar in all_calendars:
            try:
                events = await client.calendar.get_calendar_events(
                    calendar_name=calendar["name"],
                    start_date=start_date_str,
                    end_date=end_date_str,
                    limit=limit,
                )
                # Add calendar info to each event
                for event in events:
                    event["calendar_name"] = calendar["name"]
                    event["calendar_display_name"] = calendar["display_name"]
                all_events.extend(events)
            except Exception as e:
                logger.warning(
                    f"Error getting events from calendar {calendar['name']}: {e}"
                )
                continue

        # Sort by start time and limit
        all_events.sort(key=lambda x: x.get("start_datetime", ""))
        return all_events[:limit]


@mcp.tool()
async def nc_calendar_find_availability(
    duration_minutes: int,
    ctx: Context,
    attendees: str = "",  # Comma-separated email list
    date_range_start: str = "",  # "2025-07-28"
    date_range_end: str = "",  # "2025-08-04"
    business_hours_only: bool = True,
    exclude_weekends: bool = True,
    preferred_times: str = "",  # Comma-separated time ranges like "09:00-12:00,14:00-17:00"
):
    """Find available time slots for scheduling meetings.

    This tool intelligently analyzes existing calendar events to find free time slots
    that work for all specified attendees within the given constraints.

    Args:
        duration_minutes: Required duration for the meeting in minutes
        attendees: Comma-separated list of attendee email addresses to check availability for
        date_range_start: Start date for availability search (YYYY-MM-DD)
        date_range_end: End date for availability search (YYYY-MM-DD)
        business_hours_only: Only suggest slots during business hours (9 AM - 5 PM)
        exclude_weekends: Skip weekends when finding availability
        preferred_times: Preferred time ranges as "HH:MM-HH:MM" (comma-separated)

    Returns:
        List of available time slots with start/end times and duration
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client

    # Parse attendees
    attendee_list = []
    if attendees:
        attendee_list = [
            email.strip() for email in attendees.split(",") if email.strip()
        ]

    # Parse preferred times
    preferred_time_list = []
    if preferred_times:
        preferred_time_list = [
            time_range.strip()
            for time_range in preferred_times.split(",")
            if time_range.strip()
        ]

    # Build constraints
    constraints = {
        "business_hours_only": business_hours_only,
        "exclude_weekends": exclude_weekends,
        "preferred_times": preferred_time_list,
    }

    return await client.calendar.find_availability(
        duration_minutes=duration_minutes,
        attendees=attendee_list,
        date_range_start=date_range_start,
        date_range_end=date_range_end,
        constraints=constraints,
    )


@mcp.tool()
async def nc_calendar_bulk_operations(
    operation: str,  # "update", "delete", "move"
    ctx: Context,
    title_contains: Optional[str] = None,
    categories: Optional[str] = None,  # Comma-separated
    calendar_name: Optional[str] = None,
    start_date: str = "",  # "2025-07-01"
    end_date: str = "",  # "2025-07-31"
    status: Optional[str] = None,
    location_contains: Optional[str] = None,
    # Update operation parameters
    new_title: Optional[str] = None,
    new_description: Optional[str] = None,
    new_location: Optional[str] = None,
    new_categories: Optional[str] = None,
    new_priority: Optional[int] = None,
    new_reminder_minutes: Optional[int] = None,
    # Move operation parameters
    target_calendar: Optional[str] = None,
):
    """Perform bulk operations (update/delete) on events matching filter criteria.

    This tool allows you to efficiently modify or delete multiple events at once
    by applying filters to find matching events and then performing the specified operation.

    Args:
        operation: Type of operation - "update" or "delete"
        title_contains: Filter events where title contains this text
        categories: Filter events containing any of these categories (comma-separated)
        calendar_name: Filter events from this specific calendar
        start_date: Filter events starting from this date (YYYY-MM-DD)
        end_date: Filter events ending before this date (YYYY-MM-DD)
        status: Filter events by status (CONFIRMED, TENTATIVE, CANCELLED)
        location_contains: Filter events where location contains this text

        # For update operations:
        new_title: New title for matching events
        new_description: New description for matching events
        new_location: New location for matching events
        new_categories: New categories for matching events (comma-separated)
        new_priority: New priority for matching events (1-9, 5=normal)
        new_reminder_minutes: New reminder time in minutes before event

        # For move operations:
        target_calendar: Calendar to move events to (requires operation="move")

    Returns:
        Summary of operation results including counts and details
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client

    if operation not in ["update", "delete", "move"]:
        raise ValueError("Operation must be 'update', 'delete', or 'move'")

    # Build filter criteria
    filter_criteria = {}
    if title_contains is not None:
        filter_criteria["title_contains"] = title_contains
    if categories is not None:
        filter_criteria["categories"] = [cat.strip() for cat in categories.split(",")]
    if status is not None:
        filter_criteria["status"] = status
    if location_contains is not None:
        filter_criteria["location_contains"] = location_contains
    if start_date:
        filter_criteria["start_date"] = start_date
    if end_date:
        filter_criteria["end_date"] = end_date

    if operation == "delete":
        # Find matching events and delete them
        if calendar_name:
            events = await client.calendar.get_calendar_events(
                calendar_name=calendar_name, start_date=start_date, end_date=end_date
            )
            if filter_criteria:
                events = client.calendar._apply_event_filters(events, filter_criteria)
        else:
            events = await client.calendar.search_events_across_calendars(
                start_date=start_date, end_date=end_date, filters=filter_criteria
            )

        deleted_count = 0
        failed_count = 0
        results = []

        for event in events:
            try:
                await client.calendar.delete_event(
                    event.get("calendar_name", calendar_name), event["uid"]
                )
                deleted_count += 1
                results.append(
                    {
                        "uid": event["uid"],
                        "status": "deleted",
                        "title": event.get("title", ""),
                    }
                )
            except Exception as e:
                failed_count += 1
                results.append(
                    {
                        "uid": event["uid"],
                        "status": "failed",
                        "error": str(e),
                        "title": event.get("title", ""),
                    }
                )

        return {
            "operation": "delete",
            "total_found": len(events),
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "results": results,
        }

    elif operation == "update":
        # Build update data
        update_data = {}
        if new_title is not None:
            update_data["title"] = new_title
        if new_description is not None:
            update_data["description"] = new_description
        if new_location is not None:
            update_data["location"] = new_location
        if new_categories is not None:
            update_data["categories"] = new_categories
        if new_priority is not None:
            update_data["priority"] = new_priority
        if new_reminder_minutes is not None:
            update_data["reminder_minutes"] = new_reminder_minutes

        if not update_data:
            raise ValueError("No update data provided for update operation")

        return await client.calendar.bulk_update_events(filter_criteria, update_data)

    elif operation == "move":
        if not target_calendar:
            raise ValueError("target_calendar is required for move operation")

        # Find matching events
        if calendar_name:
            events = await client.calendar.get_calendar_events(
                calendar_name=calendar_name, start_date=start_date, end_date=end_date
            )
            if filter_criteria:
                events = client.calendar._apply_event_filters(events, filter_criteria)
        else:
            events = await client.calendar.search_events_across_calendars(
                start_date=start_date, end_date=end_date, filters=filter_criteria
            )

        moved_count = 0
        failed_count = 0
        results = []

        for event in events:
            try:
                # Create event in target calendar
                event_data = {
                    k: v
                    for k, v in event.items()
                    if k
                    not in [
                        "uid",
                        "href",
                        "etag",
                        "calendar_name",
                        "calendar_display_name",
                    ]
                }

                await client.calendar.create_event(target_calendar, event_data)

                # Delete from source calendar
                await client.calendar.delete_event(
                    event.get("calendar_name", calendar_name), event["uid"]
                )

                moved_count += 1
                results.append(
                    {
                        "uid": event["uid"],
                        "status": "moved",
                        "title": event.get("title", ""),
                        "from_calendar": event.get("calendar_name", calendar_name),
                        "to_calendar": target_calendar,
                    }
                )
            except Exception as e:
                failed_count += 1
                results.append(
                    {
                        "uid": event["uid"],
                        "status": "failed",
                        "error": str(e),
                        "title": event.get("title", ""),
                    }
                )

        return {
            "operation": "move",
            "total_found": len(events),
            "moved_count": moved_count,
            "failed_count": failed_count,
            "target_calendar": target_calendar,
            "results": results,
        }


@mcp.tool()
async def nc_calendar_manage_calendar(
    action: str,  # "create", "delete", "update", "list"
    ctx: Context,
    calendar_name: str = "",
    display_name: str = "",
    description: str = "",
    color: str = "#1976D2",  # Default blue color
):
    """Manage calendar creation, deletion, and properties.

    This tool provides comprehensive calendar management functionality including
    creating new calendars, deleting existing ones, and updating calendar properties.

    Args:
        action: Action to perform - "create", "delete", "update", or "list"
        calendar_name: Internal name for the calendar (required for create/delete/update)
        display_name: Human-readable name for the calendar (used for create/update)
        description: Description for the calendar (used for create/update)
        color: Hex color code for the calendar (e.g., "#1976D2" for blue)

    Returns:
        Result of the calendar management operation
    """
    client: NextcloudClient = ctx.request_context.lifespan_context.client

    if action == "list":
        return await client.calendar.list_calendars()

    elif action == "create":
        if not calendar_name:
            raise ValueError("calendar_name is required for create action")

        return await client.calendar.create_calendar(
            calendar_name=calendar_name,
            display_name=display_name or calendar_name,
            description=description,
            color=color,
        )

    elif action == "delete":
        if not calendar_name:
            raise ValueError("calendar_name is required for delete action")

        return await client.calendar.delete_calendar(calendar_name)

    elif action == "update":
        if not calendar_name:
            raise ValueError("calendar_name is required for update action")

        # Note: Calendar property updates require additional CalDAV PROPPATCH implementation
        # For now, return an informative message
        return {
            "status": "not_implemented",
            "message": "Calendar property updates require PROPPATCH implementation",
            "calendar_name": calendar_name,
            "requested_changes": {
                "display_name": display_name,
                "description": description,
                "color": color,
            },
        }

    else:
        raise ValueError("Action must be 'create', 'delete', 'update', or 'list'")


def run():
    mcp.run()


if __name__ == "__main__":
    logger.info("Starting now")
    mcp.run()
