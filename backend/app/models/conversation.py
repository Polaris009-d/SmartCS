"""
会话模型 — 参考 Chatwoot Conversation
"""
from sqlalchemy import String, Integer, Boolean, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.models.base import Base, UUIDPrimaryKey, TimestampMixin


class Conversation(Base, UUIDPrimaryKey, TimestampMixin):
    """
    对话线程 — 一个联系人在一个渠道内的完整对话。
    参考 Chatwoot: Conversation
      - display_id: Inbox 内自增序号（面向用户展示）
      - status:  open | resolved | pending | snoozed
    """
    __tablename__ = "conversations"

    display_id: Mapped[int] = mapped_column(Integer, nullable=False)
    inbox_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), nullable=False, index=True
    )
    contact_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), nullable=False, index=True
    )
    contact_inbox_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), nullable=False
    )
    assigned_agent_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True, index=True
    )

    # 状态与优先级
    status: Mapped[str] = mapped_column(
        String(20), default="open", nullable=False, index=True
    )  # open | resolved | pending | snoozed
    priority: Mapped[str] = mapped_column(
        String(20), default="medium", nullable=False
    )  # low | medium | high | urgent

    # 标题（自动截取首条消息）
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # AI 状态
    is_ai_handling: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # SLA 相关时间戳（参考 Chatwoot）
    waiting_since: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    first_reply_created_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    snoozed_until: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 扩展属性
    custom_attributes: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
