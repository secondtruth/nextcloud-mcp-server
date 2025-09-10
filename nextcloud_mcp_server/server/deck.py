import logging
from typing import Optional

from mcp.server.fastmcp import Context, FastMCP

from nextcloud_mcp_server.client import NextcloudClient
from nextcloud_mcp_server.models.deck import (
    ListBoardsResponse,
    CreateBoardResponse,
    GetBoardResponse,
)

logger = logging.getLogger(__name__)


def configure_deck_tools(mcp: FastMCP):
    """Configure Nextcloud Deck tools and resources for the MCP server."""

    # Resources
    @mcp.resource("nc://Deck/boards")
    async def deck_boards_resource():
        """List all Nextcloud Deck boards"""
        ctx: Context = mcp.get_context()
        client: NextcloudClient = ctx.request_context.lifespan_context.client
        boards = await client.deck.get_boards()
        return [board.model_dump() for board in boards]

    @mcp.resource("nc://Deck/boards/{board_id}")
    async def deck_board_resource(board_id: int):
        """Get details of a specific Nextcloud Deck board"""
        ctx: Context = mcp.get_context()
        client: NextcloudClient = ctx.request_context.lifespan_context.client
        board = await client.deck.get_board(board_id)
        return board.model_dump()

    # Tools
    @mcp.tool()
    async def deck_list_boards(
        ctx: Context, details: bool = False, if_modified_since: Optional[str] = None
    ) -> ListBoardsResponse:
        """List all Nextcloud Deck boards

        Args:
            details: Enhance boards with details about labels, stacks and users
            if_modified_since: Limit results to entities changed after this time (IMF-fixdate format)
        """
        client: NextcloudClient = ctx.request_context.lifespan_context.client
        boards = await client.deck.get_boards(
            details=details, if_modified_since=if_modified_since
        )
        return ListBoardsResponse(boards=boards, total=len(boards))

    @mcp.tool()
    async def deck_create_board(
        ctx: Context, title: str, color: str
    ) -> CreateBoardResponse:
        """Create a new Nextcloud Deck board

        Args:
            title: The title of the new board
            color: The hexadecimal color of the new board (e.g. FF0000)
        """
        client: NextcloudClient = ctx.request_context.lifespan_context.client
        board = await client.deck.create_board(title, color)
        return CreateBoardResponse(id=board.id, title=board.title, color=board.color)

    @mcp.tool()
    async def deck_get_board(ctx: Context, board_id: int) -> GetBoardResponse:
        """Get details of a specific Nextcloud Deck board

        Args:
            board_id: The ID of the board
        """
        client: NextcloudClient = ctx.request_context.lifespan_context.client
        board = await client.deck.get_board(board_id)
        return GetBoardResponse(board=board)
