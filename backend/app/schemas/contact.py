"""
联系人 Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field


class ContactCreate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    inbox_id: str | None = None
    source_id: str | None = Field(default=None, description="渠道消息来源ID")
    custom_attributes: dict = Field(default_factory=dict)


class ContactUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    custom_attributes: dict | None = None


class ContactResponse(BaseModel):
    id: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    reputation_score: float = 1.0
    custom_attributes: dict = {}
    last_activity_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContactInboxResponse(BaseModel):
    id: str
    contact_id: str
    inbox_id: str
    source_id: str
    created_at: datetime

    class Config:
        from_attributes = True
