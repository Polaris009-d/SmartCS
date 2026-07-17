"""
联系人模型 — 参考 Chatwoot Contact + ContactInbox
"""
from sqlalchemy import String, DateTime, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.models.base import Base, UUIDPrimaryKey, TimestampMixin, utcnow


class Contact(Base, UUIDPrimaryKey, TimestampMixin):
    """
    客户/访客 — 跨渠道的统一客户视图。
    参考 Chatwoot: Contact
    """
    __tablename__ = "contacts"

    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reputation_score: Mapped[float] = mapped_column(
        Float, default=1.0, nullable=False
    )  # 0.00 ~ 1.00
    custom_attributes: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )  # {"tags": ["VIP"], "source": "..."}
    last_activity_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ContactInbox(Base, UUIDPrimaryKey, TimestampMixin):
    """
    联系人与渠道的关联 — 记录客户在不同渠道中的唯一标识。
    参考 Chatwoot: ContactInbox
      - Web Widget: source_id = 浏览器生成的 UUID
      - Email:      source_id = email 地址
      - WhatsApp:   source_id = 电话号码
    """
    __tablename__ = "contact_inboxes"
    __table_args__ = (
        UniqueConstraint("contact_id", "inbox_id", name="uq_contact_inbox"),
    )

    contact_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), nullable=False, index=True
    )
    inbox_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), nullable=False, index=True
    )
    source_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # 渠道内唯一标识
    pubsub_token: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # 前端 SSE 连接令牌
