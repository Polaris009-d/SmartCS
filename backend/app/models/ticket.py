"""
工单模型
"""
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, UUIDPrimaryKey, TimestampMixin


class Ticket(Base, UUIDPrimaryKey, TimestampMixin):
    """售后工单 — 升级/转人工/投诉等"""
    __tablename__ = "tickets"

    conversation_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True, index=True)
    order_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    assigned_user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True, index=True)
    ticket_type: Mapped[str] = mapped_column(String(50), nullable=False)  # refund/address_change/complaint/escalation
    priority: Mapped[str] = mapped_column(String(20), default="normal")  # low/normal/high/urgent
    status: Mapped[str] = mapped_column(String(30), default="open")  # open/in_progress/resolved/closed
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
