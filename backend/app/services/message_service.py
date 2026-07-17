"""
消息服务 — 参考 Chatwoot MessageBuilder
处理消息创建、持久化、事件分发、AI 回复触发
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message
from app.models.conversation import Conversation
from app.schemas.message import MessageCreate
from app.services.sse_manager import sse_manager
from app.services.event_dispatcher import event_dispatcher


class MessageService:
    """
    消息构建器 — 参考 Chatwoot MessageBuilder。
    负责创建各种类型的消息（incoming/outgoing/activity），
    并在创建后触发 EventDispatcher 分发到 SSE/Webhook/Automation。
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_incoming_message(
        self,
        conversation_id: str,
        content: str,
        sender_type: str = "contact",
        sender_id: str | None = None,
        content_type: str = "text",
        source_id: str | None = None,
        content_attributes: dict | None = None,
    ) -> Message:
        """创建客户入站消息"""
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            message_type="incoming",
            content_type=content_type,
            content=content,
            sender_type=sender_type,
            sender_id=sender_id,
            source_id=source_id,
            content_attributes=content_attributes or {},
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(message)

        # 更新会话最后活动时间
        conv = await self.db.get(Conversation, conversation_id)
        if conv:
            conv.last_activity_at = datetime.now(timezone.utc)
            # resolved/snoozed 会话收到新消息 → reopen
            if conv.status in ("resolved", "snoozed"):
                conv.status = "open"
                conv.resolved_at = None
                conv.snoozed_until = None

        await self.db.flush()

        # 事件分发
        msg_data = self._message_to_dict(message)
        await event_dispatcher.dispatch("message.created", msg_data)

        # SSE 实时推送
        await sse_manager.publish(conversation_id, "message.created", msg_data)

        return message

    async def create_outgoing_message(
        self,
        conversation_id: str,
        content: str,
        sender_type: str = "agent",
        sender_id: str | None = None,
        content_type: str = "text",
        private: bool = False,
        ai_confidence: float | None = None,
        content_attributes: dict | None = None,
    ) -> Message:
        """创建客服/AI/系统出站消息"""
        now = datetime.now(timezone.utc)
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            message_type="outgoing",
            content_type=content_type,
            content=content,
            private=private,
            sender_type=sender_type,
            sender_id=sender_id,
            ai_confidence=ai_confidence,
            content_attributes=content_attributes or {},
            created_at=now,
        )
        self.db.add(message)

        # 更新会话
        conv = await self.db.get(Conversation, conversation_id)
        if conv:
            conv.last_activity_at = now

        await self.db.flush()

        # 非内部备注才推送
        if not private:
            msg_data = self._message_to_dict(message)
            await event_dispatcher.dispatch("message.created", msg_data)
            await sse_manager.publish(conversation_id, "message.created", msg_data)

        return message

    async def create_activity_message(
        self,
        conversation_id: str,
        content: str,
        content_attributes: dict | None = None,
    ) -> Message:
        """创建系统活动消息（分配/状态变更/转接等）"""
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            message_type="activity",
            content_type="text",
            content=content,
            sender_type="system",
            sender_id=None,
            content_attributes=content_attributes or {},
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(message)
        await self.db.flush()

        msg_data = self._message_to_dict(message)
        await sse_manager.publish(conversation_id, "message.created", msg_data)
        return message

    async def create_ai_message(
        self,
        conversation_id: str,
        content: str,
        ai_confidence: float | None = None,
        content_attributes: dict | None = None,
    ) -> Message:
        """创建 AI 回复消息"""
        return await self.create_outgoing_message(
            conversation_id=conversation_id,
            content=content,
            sender_type="ai",
            sender_id=None,
            content_type="text",
            ai_confidence=ai_confidence,
            content_attributes=content_attributes or {},
        )

    async def get_message(self, message_id: str) -> Message | None:
        result = await self.db.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def mark_as_read(self, conversation_id: str) -> None:
        """标记会话中所有客户消息为已读"""
        from sqlalchemy import update
        await self.db.execute(
            update(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.sender_type == "contact",
                Message.is_read == False,
            )
            .values(is_read=True)
        )
        await self.db.flush()

    def _message_to_dict(self, message: Message) -> dict:
        """将 Message ORM 对象转为可序列化的 dict"""
        return {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "message_type": message.message_type,
            "content_type": message.content_type,
            "content": message.content,
            "private": message.private,
            "sender_type": message.sender_type,
            "sender_id": message.sender_id,
            "source_id": message.source_id,
            "content_attributes": message.content_attributes,
            "ai_confidence": message.ai_confidence,
            "sentiment_score": message.sentiment_score,
            "is_read": message.is_read,
            "created_at": message.created_at.isoformat() if message.created_at else None,
        }
