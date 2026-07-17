"""
渠道 Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field


class InboxCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    channel_type: str = Field(..., pattern="^(web_widget|api)$")
    channel_config: dict = Field(default_factory=dict)
    auto_assignment_enabled: bool = True
    assignment_algorithm: str = Field(default="round_robin", pattern="^(round_robin|balanced)$")
    greeting_message: str | None = None


class InboxUpdate(BaseModel):
    name: str | None = None
    channel_config: dict | None = None
    auto_assignment_enabled: bool | None = None
    assignment_algorithm: str | None = Field(default=None, pattern="^(round_robin|balanced)$")
    greeting_message: str | None = None
    is_active: bool | None = None


class InboxResponse(BaseModel):
    id: str
    name: str
    channel_type: str
    channel_config: dict
    auto_assignment_enabled: bool
    assignment_algorithm: str
    greeting_message: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
