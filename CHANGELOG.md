## [Unreleased]

### Feat

- **calendar**: Add comprehensive Calendar app support via CalDAV protocol (Issue #74)
- **calendar**: Add `nc_calendar_list_calendars` tool for listing available calendars
- **calendar**: Add `nc_calendar_create_event` tool with full feature support (recurrence, reminders, attendees, categories)
- **calendar**: Add `nc_calendar_list_events` tool with advanced filtering (date range, attendees, categories, status)
- **calendar**: Add `nc_calendar_get_event` tool for retrieving detailed event information
- **calendar**: Add `nc_calendar_update_event` tool for modifying existing events
- **calendar**: Add `nc_calendar_delete_event` tool for removing events
- **calendar**: Add `nc_calendar_create_meeting` tool for quick meeting creation with smart defaults
- **calendar**: Add `nc_calendar_get_upcoming_events` tool for viewing upcoming events
- **calendar**: Add `nc_calendar_find_availability` tool for intelligent scheduling assistance
- **calendar**: Add `nc_calendar_bulk_operations` tool for efficient batch event management
- **calendar**: Add `nc_calendar_manage_calendar` tool for calendar creation and management

### Fix

- **calendar**: Fix type annotations in calendar client for better Pylance compatibility
- **calendar**: Fix alarm trigger formatting using proper timedelta objects
- **calendar**: Fix event update handling to merge existing data with new changes
- **calendar**: Fix categories extraction from icalendar objects

### Refactor

- **calendar**: Implement CalDAV client following existing NextCloud client patterns
- **calendar**: Add comprehensive calendar integration tests covering all scenarios

## v0.5.0 (2025-07-26)

### Feat

- Update webdav client create_directory method to handle recursive directories
- **webdav**: add complete file system support

### Fix

- apply ruff formatting to test_webdav_operations.py

## v0.4.1 (2025-07-10)

### Fix

- **deps**: update dependency mcp to >=1.10,<1.11

## v0.4.0 (2025-07-06)

### Feat

- Add TablesClient and associated tools

### Fix

- update tests

### Refactor

- Modularize NC and Notes app client

## v0.3.0 (2025-06-06)

### Feat

- Switch to using async client

## v0.2.5 (2025-05-25)

### Fix

- Commitizen release process

## v0.2.4 (2025-05-25)

### Fix

- Do not update dependencies when running in Dockerfile
- Configure logging

## v0.2.3 (2025-05-25)

### Fix

- Limit search results to notes with score > 0.5

## v0.2.2 (2025-05-24)

### Fix

- Install deps before checking service

## v0.2.1 (2025-05-24)

### Fix

- Install deps before checking service

## v0.2.1 (2025-05-24)

## v0.2.0 (2025-05-24)

### Feat

- **notes**: Add append to note functionality

### Fix

- **deps**: update dependency mcp to >=1.9,<1.10

## v0.1.3 (2025-05-16)

## v0.1.2 (2025-05-05)

## v0.1.1 (2025-05-05)

## v0.1.0 (2025-05-05)
