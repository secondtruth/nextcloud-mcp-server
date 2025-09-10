# Nextcloud MCP Server

[![Docker Image](https://img.shields.io/badge/docker-ghcr.io/cbcoutinho/nextcloud--mcp--server-blue)](https://github.com/cbcoutinho/nextcloud-mcp-server/pkgs/container/nextcloud-mcp-server)

The Nextcloud MCP (Model Context Protocol) server allows Large Language Models (LLMs) like OpenAI's GPT, Google's Gemini, or Anthropic's Claude to interact with your Nextcloud instance. This enables automation of various Nextcloud actions, starting with the Notes API.

## Features

The server provides integration with multiple Nextcloud apps, enabling LLMs to interact with your Nextcloud data through a rich set of tools and resources.

## Supported Nextcloud Apps

| App | Support Status | Description |
|-----|----------------|-------------|
| **Notes** | ✅ Full Support | Create, read, update, delete, and search notes. Handle attachments via WebDAV. |
| **Calendar** | ✅ Full Support | Complete calendar integration - create, update, delete events. Support for recurring events, reminders, attendees, and all-day events via CalDAV. |
| **Tables** | ⚠️ Row Operations | Read table schemas and perform CRUD operations on table rows. Table management not yet supported. |
| **Files (WebDAV)** | ✅ Full Support | Complete file system access - browse directories, read/write files, create/delete resources. |
| **Contacts** | ✅ Full Support | Create, read, update, and delete contacts and address books via CardDAV. |
| **Deck** | ❌ [Not Started](https://github.com/cbcoutinho/nextcloud-mcp-server/issues/75) | TBD |
| **Tasks** | ❌ [Not Started](https://github.com/cbcoutinho/nextcloud-mcp-server/issues/73) | TBD |

Is there a Nextcloud app not present in this list that you'd like to be
included? Feel free to open an issue, or contribute via a pull-request.

## Available Tools

### Notes Tools

| Tool | Description |
|------|-------------|
| `nc_get_note` | Get a specific note by ID |
| `nc_notes_create_note` | Create a new note with title, content, and category |
| `nc_notes_update_note` | Update an existing note by ID |
| `nc_notes_append_content` | Append content to an existing note with a clear separator |
| `nc_notes_delete_note` | Delete a note by ID |
| `nc_notes_search_notes` | Search notes by title or content |

### Calendar Tools

| Tool | Description |
|------|-------------|
| `nc_calendar_list_calendars` | List all available calendars for the user |
| `nc_calendar_create_event` | Create a comprehensive calendar event with full feature support (recurring, reminders, attendees, etc.) |
| `nc_calendar_list_events` | **Enhanced:** List events with advanced filtering (min attendees, duration, categories, status, search across all calendars) |
| `nc_calendar_get_event` | Get detailed information about a specific event |
| `nc_calendar_update_event` | Update any aspect of an existing event |
| `nc_calendar_delete_event` | Delete a calendar event |
| `nc_calendar_create_meeting` | Quick meeting creation with smart defaults |
| `nc_calendar_get_upcoming_events` | Get upcoming events in the next N days |
| `nc_calendar_find_availability` | **New:** Intelligent availability finder - find free time slots for meetings with attendee conflict detection |
| `nc_calendar_bulk_operations` | **New:** Bulk update, delete, or move events matching filter criteria |
| `nc_calendar_manage_calendar` | **New:** Create, delete, and manage calendar properties |

### Contacts Tools

| Tool | Description |
|------|-------------|
| `nc_contacts_list_addressbooks` | List all available addressbooks for the user |
| `nc_contacts_list_contacts` | List all contacts in a specific addressbook |
| `nc_contacts_create_addressbook` | Create a new addressbook |
| `nc_contacts_delete_addressbook` | Delete an addressbook |
| `nc_contacts_create_contact` | Create a new contact in an addressbook |
| `nc_contacts_delete_contact` | Delete a contact from an addressbook |

### Tables Tools

| Tool | Description |
|------|-------------|
| `nc_tables_list_tables` | List all tables available to the user |
| `nc_tables_get_schema` | Get the schema/structure of a specific table including columns and views |
| `nc_tables_read_table` | Read rows from a table with optional pagination |
| `nc_tables_insert_row` | Insert a new row into a table |
| `nc_tables_update_row` | Update an existing row in a table |
| `nc_tables_delete_row` | Delete a row from a table |

### WebDAV File System Tools

| Tool | Description |
|------|-------------|
| `nc_webdav_list_directory` | List files and directories in any NextCloud path |
| `nc_webdav_read_file` | Read file content (text files decoded, binary as base64) |
| `nc_webdav_write_file` | Create or update files in NextCloud |
| `nc_webdav_create_directory` | Create new directories |
| `nc_webdav_delete_resource` | Delete files or directories |

## Available Resources

| Resource | Description |
|----------|-------------|
| `nc://capabilities` | Access Nextcloud server capabilities |
| `notes://settings` | Access Notes app settings |
| `nc://Notes/{note_id}/attachments/{attachment_filename}` | Access attachments for notes |

### WebDAV File System Access

The server provides complete file system access to your NextCloud instance, enabling you to:

- Browse any directory structure
- Read and write files of any type
- Create and delete directories
- Manage your NextCloud files directly through LLM interactions

**Usage Examples:**

```python
# List files in root directory
await nc_webdav_list_directory("")

# Browse a specific folder
await nc_webdav_list_directory("Documents/Projects")

# Read a text file
content = await nc_webdav_read_file("Documents/readme.txt")

# Create a new directory
await nc_webdav_create_directory("NewProject/docs")

# Write content to a file
await nc_webdav_write_file("NewProject/docs/notes.md", "# My Notes\n\nContent here...")

# Delete a file or directory
await nc_webdav_delete_resource("old_file.txt")
```

### Calendar Integration

The server provides comprehensive calendar integration through CalDAV, enabling you to:

- List all available calendars
- Create, read, update, and delete calendar events  
- Handle recurring events with RRULE support
- Manage event reminders and notifications
- Support all-day and timed events
- Handle attendees and meeting invitations
- Organize events with categories and priorities

**Usage Examples:**

```python
# List available calendars
calendars = await nc_calendar_list_calendars()

# Create a simple event
await nc_calendar_create_event(
    calendar_name="personal",
    title="Team Meeting", 
    start_datetime="2025-07-28T14:00:00",
    end_datetime="2025-07-28T15:00:00",
    description="Weekly team sync",
    location="Conference Room A"
)

# Create a recurring weekly meeting
await nc_calendar_create_event(
    calendar_name="work",
    title="Weekly Standup",
    start_datetime="2025-07-28T09:00:00", 
    end_datetime="2025-07-28T09:30:00",
    recurring=True,
    recurrence_rule="FREQ=WEEKLY;BYDAY=MO"
)

# Quick meeting creation
await nc_calendar_create_meeting(
    title="Client Call",
    date="2025-07-28",
    time="15:00",
    duration_minutes=60,
    attendees="client@example.com,colleague@company.com"
)

# Get upcoming events  
events = await nc_calendar_get_upcoming_events(days_ahead=7)

# Advanced search - find all meetings with 5+ attendees lasting 2+ hours
long_meetings = await nc_calendar_list_events(
    calendar_name="",  # Search all calendars
    search_all_calendars=True,
    start_date="2025-07-01",
    end_date="2025-07-31", 
    min_attendees=5,
    min_duration_minutes=120,
    title_contains="meeting"
)

# Find availability for a 1-hour meeting with specific attendees
availability = await nc_calendar_find_availability(
    duration_minutes=60,
    attendees="sarah@company.com,mike@company.com",
    date_range_start="2025-07-28",
    date_range_end="2025-08-04",
    business_hours_only=True,
    exclude_weekends=True,
    preferred_times="09:00-12:00,14:00-17:00"
)

# Bulk update all team meetings to new location
bulk_result = await nc_calendar_bulk_operations(
    operation="update",
    title_contains="team meeting",
    start_date="2025-08-01", 
    end_date="2025-08-31",
    new_location="Conference Room B",
    new_reminder_minutes=15
)

# Create a new project calendar
new_calendar = await nc_calendar_manage_calendar(
    action="create",
    calendar_name="project-alpha",
    display_name="Project Alpha Calendar",
    description="Calendar for Project Alpha team",
    color="#FF5722"
)
```

### Note Attachments

This server supports adding and retrieving note attachments via WebDAV. Please note the following behavior regarding attachments:

* When a note is deleted, its attachments remain in the system. This matches the behavior of the official Nextcloud Notes app.
* Orphaned attachments (attachments whose parent notes have been deleted) may accumulate over time.
* WebDAV permissions must be properly configured for attachment operations to work correctly.

## Installation

### Prerequisites

*   Python 3.8+
*   Access to a Nextcloud instance

### Local Installation

1.  Clone the repository (if running from source):
    ```bash
    git clone https://github.com/cbcoutinho/nextcloud-mcp-server.git
    cd nextcloud-mcp-server
    ```
2.  Install the package dependencies (if running via CLI):
    ```bash
    uv sync
    ```

### Docker

A pre-built Docker image is available: `ghcr.io/cbcoutinho/nextcloud-mcp-server`

## Configuration

The server requires credentials to connect to your Nextcloud instance. Create a file named `.env` (or any name you prefer) in the directory where you'll run the server, based on the `env.sample` file:

```dotenv
# .env
NEXTCLOUD_HOST=https://your.nextcloud.instance.com
NEXTCLOUD_USERNAME=your_nextcloud_username
NEXTCLOUD_PASSWORD=your_nextcloud_app_password_or_login_password
```

*   `NEXTCLOUD_HOST`: The full URL of your Nextcloud instance.
*   `NEXTCLOUD_USERNAME`: Your Nextcloud username.
*   `NEXTCLOUD_PASSWORD`: **Important:** It is highly recommended to use a dedicated Nextcloud App Password for security. You can generate one in your Nextcloud Security settings. Alternatively, you can use your regular login password, but this is less secure.

## Running the Server

### Locally

Ensure your environment variables are loaded, then run the server. You have several options:

#### Option 1: Using `nextcloud_mcp_server` cli (recommended)
```bash
# Load environment variables from your .env file
export $(grep -v '^#' .env | xargs)

# Or run the app module directly with custom options
uv run python -m nextcloud_mcp_server.app --host 0.0.0.0 --port 8080 --log-level info --reload

# Enable only specific Nextcloud app APIs
uv run python -m nextcloud_mcp_server.app --enable-app notes --enable-app calendar

# Enable only WebDAV for file operations
uv run python -m nextcloud_mcp_server.app --enable-app webdav
```

#### Option 2: Using `uvicorn`

You can also run the MCP server with `uvicorn` directly, which enables support
for all uvicorn arguments (e.g. `--reload`, `--workers`).

```bash
# Load environment variables from your .env file
export $(grep -v '^#' .env | xargs)

# Run with uvicorn using the --factory option
uv run uvicorn nextcloud_mcp_server.app:get_app --factory --reload --host 127.0.0.1 --port 8000
```

The server will start, typically listening on `http://127.0.0.1:8000`.

**Host binding options:**
- Use `--host 0.0.0.0` to bind to all interfaces
- Use `--host 127.0.0.1` to bind only to localhost (default)

See the full list of available `uvicorn` options and how to set them at [https://www.uvicorn.org/settings/]()

### Selective App Enablement

By default, all supported Nextcloud app APIs are enabled. You can selectively enable only specific apps using the `--enable-app` option:

```bash
# Available apps: notes, tables, webdav, calendar, contacts

# Enable all apps (default behavior)
uv run python -m nextcloud_mcp_server.app

# Enable only Notes and Calendar
uv run python -m nextcloud_mcp_server.app --enable-app notes --enable-app calendar

# Enable only WebDAV for file operations
uv run python -m nextcloud_mcp_server.app --enable-app webdav

# Enable multiple apps by repeating the option
uv run python -m nextcloud_mcp_server.app --enable-app notes --enable-app tables --enable-app contacts
```

This can be useful for:
- Reducing memory usage and startup time
- Limiting available functionality for security or organizational reasons
- Testing specific app integrations
- Running lightweight instances with only needed features

### Using Docker

Mount your environment file when running the container:

```bash
# Run with all apps enabled (default)
docker run -p 127.0.0.1:8000:8000 --env-file .env --rm ghcr.io/cbcoutinho/nextcloud-mcp-server:latest \
  --host 0.0.0.0

# Run with only specific apps enabled
docker run -p 127.0.0.1:8000:8000 --env-file .env --rm ghcr.io/cbcoutinho/nextcloud-mcp-server:latest \
  --host 0.0.0.0 --enable-app notes --enable-app calendar

# Run with only WebDAV
docker run -p 127.0.0.1:8000:8000 --env-file .env --rm ghcr.io/cbcoutinho/nextcloud-mcp-server:latest \
  --host 0.0.0.0 --enable-app webdav
```

This will start the server and expose it on port 8000 of your local machine.

## Usage

Once the server is running, you can connect to it using an MCP client like `MCP Inspector`. Once your MCP server is running, launch MCP Inspector as follows:

```bash
uv run mcp dev
```

You can then connect to and interact with the server's tools and resources through your browser.

## References:

- https://github.com/modelcontextprotocol/python-sdk

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests on the [GitHub repository](https://github.com/cbcoutinho/nextcloud-mcp-server).

## License

This project is licensed under the AGPL-3.0 License. See the [LICENSE](./LICENSE) file for details.

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/cbcoutinho-nextcloud-mcp-server-badge.png)](https://mseep.ai/app/cbcoutinho-nextcloud-mcp-server)
