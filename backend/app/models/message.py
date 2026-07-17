"""
消息模型 — 参考 Chatwoot Message
"""
from sqlalchemy import String, Text, Boolean, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.models.base import Base, UUIDPrimaryKey


class Message(Base, UUIDPrimaryKey):
    """
    单条消息 — 支持多态发送者与多种消息类型。
    参考 Chatwoot: Message
      - message_type:  incoming | outgoing | activity | template
      - content_type:  text | image | rich | cards | agent_action
      - private:       内部备注（客户不可见）
      - sender:        多态 (user / contact / ai / system)
    """
    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), nullable=False, index=True
    )

    # 消息分类
    message_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="incoming"
    )  # incoming | outgoing | activity | template
    content_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="text"
    )  # text | image | rich | cards | agent_action

    # 内容
    content: Mapped[str] = mapped_column(Text, nullable=False)
    private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 多态发送者
    sender_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # user | contact | ai | system | agent_bot
    sender_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True
    )

    # 渠道消息 ID（去重用）
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # 扩展属性（附件 URL、卡片数据、Agent 步骤等）
    content_attributes: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    # AI 相关
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 阅读状态
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 时间戳（消息只有创建时间，不更新）
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
