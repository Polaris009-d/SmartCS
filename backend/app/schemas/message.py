"""
消息 Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, description="消息内容")
    message_type: str = Field(default="outgoing", pattern="^(incoming|outgoing)$")
    content_type: str = Field(default="text", pattern="^(text|image|rich|agent_action)$")
    private: bool = False
    source_id: str | None = None
    content_attributes: dict = Field(default_factory=dict)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    message_type: str
    content_type: str
    content: str
    private: bool = False
    sender_type: str
    sender_id: str | None = None
    source_id: str | None = None
    content_attributes: dict = {}
    ai_confidence: float | None = None
    sentiment_score: float | None = None
    is_read: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class SSEEvent(BaseModel):
    """SSE 事件协议"""
    event: str  # message.created | ai_chunk | ai_done | agent_action | conversation.updated | handoff | typing | keepalive
    data: dict
