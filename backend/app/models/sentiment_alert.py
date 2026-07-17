"""
情感预警模型
"""
from sqlalchemy import String, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, UUIDPrimaryKey


class SentimentAlert(Base, UUIDPrimaryKey):
    """情感预警记录"""
    __tablename__ = "sentiment_alerts"

    conversation_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    message_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    sentiment_label: Mapped[str] = mapped_column(String(20), nullable=False)  # negative / very_negative
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False)
    alert_level: Mapped[str] = mapped_column(String(20), default="warning")  # info / warning / critical
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_ticket_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    handled_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    handled_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
