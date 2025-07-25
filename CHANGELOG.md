## [Unreleased]

### Feat

- **webdav**: Add complete file system support with directory browsing, file read/write, and resource management
- **webdav**: Add `nc_webdav_list_directory` tool for browsing any NextCloud directory
- **webdav**: Add `nc_webdav_read_file` tool with automatic text/binary content handling
- **webdav**: Add `nc_webdav_write_file` tool supporting text and base64 binary content
- **webdav**: Add `nc_webdav_create_directory` tool for creating directories
- **webdav**: Add `nc_webdav_delete_resource` tool for deleting files and directories
- **webdav**: Add XML parsing for WebDAV PROPFIND responses with metadata extraction

### Fix

- **types**: Improve type annotations throughout codebase for better IDE support
- **types**: Fix Context parameter ordering in MCP tools (required before optional)
- **types**: Add proper type hints for WebDAV client methods

### Refactor

- **webdav**: Extend WebDAV client beyond Notes attachments to general file operations
- **server**: Enhance error handling and logging for WebDAV operations

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
