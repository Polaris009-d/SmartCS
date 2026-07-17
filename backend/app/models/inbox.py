"""
渠道模型 — 参考 Chatwoot Inbox + Channel 多态设计
"""
from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import Base, UUIDPrimaryKey, TimestampMixin


class Inbox(Base, UUIDPrimaryKey, TimestampMixin):
    """
    渠道容器 — 统一管理不同渠道的配置。
    channel_type 决定使用哪个 Channel 策略对象。
    参考 Chatwoot: Inbox has_one :channel (polymorphic)
    """
    __tablename__ = "inboxes"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    channel_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # web_widget | api | email
    channel_config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )  # 渠道特定配置（API key、webhook URL 等）
    auto_assignment_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    assignment_algorithm: Mapped[str] = mapped_column(
        String(50), default="round_robin", nullable=False
    )  # round_robin | balanced
    working_hours_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    greeting_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
