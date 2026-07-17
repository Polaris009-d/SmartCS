"""
会话 Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.message import MessageResponse


class ConversationCreate(BaseModel):
    inbox_id: str
    contact_id: str | None = None
    source_id: str | None = Field(default=None, description="ContactInbox source_id")
    title: str | None = Field(default=None, max_length=500)
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")


class ConversationUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(open|resolved|pending|snoozed)$")
    priority: str | None = Field(default=None, pattern="^(low|medium|high|urgent)$")
    assigned_agent_id: str | None = None
    title: str | None = Field(default=None, max_length=500)
    is_ai_handling: bool | None = None


class ConversationFilter(BaseModel):
    inbox_id: str | None = None
    status: str | None = None
    assigned_agent_id: str | None = None
    contact_id: str | None = None
    priority: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ConversationResponse(BaseModel):
    id: str
    display_id: int
    inbox_id: str
    contact_id: str
    assigned_agent_id: str | None = None
    status: str
    priority: str
    title: str | None = None
    is_ai_handling: bool = True
    ai_confidence: float | None = None
    waiting_since: datetime | None = None
    first_reply_created_at: datetime | None = None
    snoozed_until: datetime | None = None
    last_activity_at: datetime | None = None
    resolved_at: datetime | None = None
    custom_attributes: dict = {}
    contact_name: str | None = None
    contact_email: str | None = None
    unread_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = []
