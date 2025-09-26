import logging

from mcp.server.fastmcp import Context, FastMCP

from nextcloud_mcp_server.client import NextcloudClient
from nextcloud_mcp_server.utils import get_nc_client

logger = logging.getLogger(__name__)


def configure_tables_tools(mcp: FastMCP):
    # Tables tools
    @mcp.tool()
    async def nc_tables_list_tables(ctx: Context):
        """List all tables available to the user"""
        client: NextcloudClient = get_nc_client(ctx)
        return await client.tables.list_tables()

    @mcp.tool()
    async def nc_tables_get_schema(table_id: int, ctx: Context):
        """Get the schema/structure of a specific table including columns and views"""
        client: NextcloudClient = get_nc_client(ctx)
        return await client.tables.get_table_schema(table_id)

    @mcp.tool()
    async def nc_tables_read_table(
        table_id: int,
        ctx: Context,
        limit: int | None = None,
        offset: int | None = None,
    ):
        """Read rows from a table with optional pagination"""
        client: NextcloudClient = get_nc_client(ctx)
        return await client.tables.get_table_rows(table_id, limit, offset)

    @mcp.tool()
    async def nc_tables_insert_row(table_id: int, data: dict, ctx: Context):
        """Insert a new row into a table.

        Data should be a dictionary mapping column IDs to values, e.g. {1: "text", 2: 42}
        """
        client: NextcloudClient = get_nc_client(ctx)
        return await client.tables.create_row(table_id, data)

    @mcp.tool()
    async def nc_tables_update_row(row_id: int, data: dict, ctx: Context):
        """Update an existing row in a table.

        Data should be a dictionary mapping column IDs to new values, e.g. {1: "new text", 2: 99}
        """
        client: NextcloudClient = get_nc_client(ctx)
        return await client.tables.update_row(row_id, data)

    @mcp.tool()
    async def nc_tables_delete_row(row_id: int, ctx: Context):
        """Delete a row from a table"""
        client: NextcloudClient = get_nc_client(ctx)
        return await client.tables.delete_row(row_id)
