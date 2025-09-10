from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from pydantic import BaseModel, Field, field_validator

from .base import BaseResponse, StatusResponse


class DeckUser(BaseModel):
    primaryKey: str
    uid: str
    displayname: str


class DeckPermissions(BaseModel):
    PERMISSION_READ: bool
    PERMISSION_EDIT: bool
    PERMISSION_MANAGE: bool
    PERMISSION_SHARE: bool


class DeckLabel(BaseModel):
    id: int
    title: str
    color: str
    boardId: Optional[int] = None
    cardId: Optional[int] = None


class DeckACL(BaseModel):
    id: int
    participant: DeckUser
    type: int
    boardId: int
    permissionEdit: bool
    permissionShare: bool
    permissionManage: bool
    owner: bool


class DeckBoardSettings(BaseModel):
    calendar: bool
    cardDetailsInModal: Optional[bool] = Field(default=None, alias="cardDetailsInModal")
    cardIdBadge: Optional[bool] = Field(default=None, alias="cardIdBadge")
    groupLimit: Optional[List[Dict[str, str]]] = Field(default=None, alias="groupLimit")
    notify_due: Optional[str] = Field(default=None, alias="notify-due")


class DeckBoard(BaseModel):
    id: int
    title: str
    owner: DeckUser
    color: str
    archived: bool
    labels: List[DeckLabel]
    acl: List[DeckACL]
    permissions: DeckPermissions
    users: List[DeckUser]
    deletedAt: int
    lastModified: Optional[int] = None
    settings: Optional[DeckBoardSettings] = None
    etag: Optional[str] = Field(default=None, alias="ETag")

    @field_validator("settings", mode="before")
    @classmethod
    def validate_settings(cls, v):
        # Handle case where API returns empty array instead of dict/null
        if isinstance(v, list) and len(v) == 0:
            return None
        return v


class DeckCard(BaseModel):
    id: int
    title: str
    stackId: int
    type: str
    order: int
    archived: bool
    owner: Union[str, DeckUser]  # Can be either string or user object
    description: Optional[str] = None
    duedate: Optional[datetime] = None
    done: Optional[datetime] = None
    lastModified: Optional[int] = None
    createdAt: Optional[int] = None
    labels: Optional[List[DeckLabel]] = None
    assignedUsers: Optional[List[DeckUser]] = None
    attachments: Optional[List[Any]] = None  # Define a proper Attachment model later
    attachmentCount: Optional[int] = None
    deletedAt: Optional[int] = None
    commentsUnread: Optional[int] = None
    overdue: Optional[int] = None
    etag: Optional[str] = Field(default=None, alias="ETag")

    @field_validator("owner", mode="before")
    @classmethod
    def validate_owner(cls, v):
        # Handle case where API returns user object instead of string
        if isinstance(v, dict):
            return v.get("uid", v.get("primaryKey", str(v)))
        return v


class DeckStack(BaseModel):
    id: int
    title: str
    boardId: int
    order: int
    deletedAt: int
    lastModified: Optional[int] = None
    cards: Optional[List[DeckCard]] = None
    etag: Optional[str] = Field(default=None, alias="ETag")


class DeckAttachmentExtendedData(BaseModel):
    filesize: int
    mimetype: str
    info: Dict[str, str]


class DeckAttachment(BaseModel):
    id: int
    cardId: int
    type: str
    data: str
    lastModified: int
    createdAt: int
    createdBy: str
    deletedAt: int
    extendedData: DeckAttachmentExtendedData


class DeckComment(BaseModel):
    id: int
    objectId: int
    message: str
    actorId: str
    actorType: str
    actorDisplayName: str
    creationDateTime: datetime
    mentions: List[Dict[str, str]]
    replyTo: Optional[Any] = None  # Self-referencing, handle later if needed


class DeckSession(BaseModel):
    token: str


class DeckConfig(BaseModel):
    calendar: bool
    cardDetailsInModal: bool
    cardIdBadge: bool
    groupLimit: Optional[List[Dict[str, str]]] = None


# Response Models for MCP Tools


class ListBoardsResponse(BaseResponse):
    """Response model for listing deck boards."""

    boards: List[DeckBoard] = Field(description="List of deck boards")
    total: int = Field(description="Total number of boards")


class CreateBoardResponse(BaseResponse):
    """Response model for board creation."""

    id: int = Field(description="The created board ID")
    title: str = Field(description="The created board title")
    color: str = Field(description="The created board color")


class GetBoardResponse(BaseResponse):
    """Response model for getting board details."""

    board: DeckBoard = Field(description="Board details")


class BoardOperationResponse(StatusResponse):
    """Response model for board operations like update/delete."""

    board_id: int = Field(description="ID of the affected board")
