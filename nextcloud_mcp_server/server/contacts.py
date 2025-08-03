import logging

from mcp.server.fastmcp import Context, FastMCP

from nextcloud_mcp_server.client import NextcloudClient

logger = logging.getLogger(__name__)


def configure_contacts_tools(mcp: FastMCP):
    # Contacts tools
    @mcp.tool()
    async def nc_contacts_list_addressbooks(ctx: Context):
        """List all addressbooks for the user."""
        client: NextcloudClient = ctx.request_context.lifespan_context.client
        return await client.contacts.list_addressbooks()

    @mcp.tool()
    async def nc_contacts_list_contacts(ctx: Context, *, addressbook: str):
        """List all addressbooks for the user."""
        client: NextcloudClient = ctx.request_context.lifespan_context.client
        return await client.contacts.list_contacts(addressbook=addressbook)
