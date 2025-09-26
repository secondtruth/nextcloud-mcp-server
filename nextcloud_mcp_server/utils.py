"""Utilities for the Nextcloud MCP Server."""

import logging
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context
from mcp.shared.exceptions import McpError

if TYPE_CHECKING:
    from nextcloud_mcp_server.client import NextcloudClient

logger = logging.getLogger(__name__)


def get_nc_client(ctx: Context) -> "NextcloudClient":
    """Get the appropriate NextcloudClient for the current request.
    
    In single-user mode: returns the global client from lifespan context
    In multi-user mode: returns the per-request client from request state
    
    Args:
        ctx: The MCP context for the current request
        
    Returns:
        NextcloudClient: The client instance to use for this request
        
    Raises:
        McpError: If in multi-user mode and no client is attached to the request
    """
    app_context = ctx.request_context.lifespan_context
    
    if app_context.multi_user_mode:
        # Multi-user mode: get client from request state
        # Access request state through the context
        if hasattr(ctx.request_context, 'request') and hasattr(ctx.request_context.request.state, 'nc_client'):
            return ctx.request_context.request.state.nc_client
        else:
            raise McpError(
                code=-32600,
                message="Request missing authentication. Authorization header required in multi-user mode."
            )
    else:
        # Single-user mode: use global client
        return app_context.client