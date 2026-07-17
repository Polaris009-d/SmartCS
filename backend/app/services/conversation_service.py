"""
会话服务 — 参考 Chatwoot Conversation 状态机
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.services.assignment_service import AssignmentService


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_conversations(
        self,
        inbox_id: str | None = None,
        status: str | None = None,
        assigned_agent_id: str | None = None,
        contact_id: str | None = None,
        priority: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Conversation], int]:
        """按条件筛选会话列表"""
        conditions = []
        if inbox_id:
            conditions.append(Conversation.inbox_id == inbox_id)
        if status:
            conditions.append(Conversation.status == status)
        if assigned_agent_id:
            conditions.append(Conversation.assigned_agent_id == assigned_agent_id)
        if contact_id:
            conditions.append(Conversation.contact_id == contact_id)
        if priority:
            conditions.append(Conversation.priority == priority)

        where_clause = (*conditions,) if conditions else (True,)

        total_q = select(func.count()).select_from(Conversation).where(*where_clause)
        total = (await self.db.execute(total_q)).scalar() or 0

        items_q = (
            select(Conversation)
            .where(*where_clause)
            .order_by(desc(Conversation.last_activity_at).nulls_last())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(items_q)
        return list(result.scalars().all()), total

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def create_conversation(
        self,
        inbox_id: str,
        contact_id: str,
        contact_inbox_id: str,
        title: str | None = None,
        priority: str = "medium",
    ) -> Conversation:
        """创建新会话，自动生成 display_id"""
        # 生成 Inbox 内自增 display_id
        max_display_q = select(func.coalesce(func.max(Conversation.display_id), 0)).where(
            Conversation.inbox_id == inbox_id
        )
        max_display = (await self.db.execute(max_display_q)).scalar() or 0

        now = datetime.now(timezone.utc)
        conversation = Conversation(
            display_id=max_display + 1,
            inbox_id=inbox_id,
            contact_id=contact_id,
            contact_inbox_id=contact_inbox_id,
            title=title or "新会话",
            priority=priority,
            status="pending",  # AI 先处理
            is_ai_handling=True,
            last_activity_at=now,
        )
        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation

    async def find_or_create_conversation(
        self,
        inbox_id: str,
        contact_id: str,
        contact_inbox_id: str,
        title: str | None = None,
    ) -> Conversation:
        """查找最近活跃的 open/pending 会话，没有则创建新会话"""
        # 查找该联系人在该渠道是否有活跃会话
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.inbox_id == inbox_id,
                Conversation.contact_id == contact_id,
                Conversation.status.in_(["open", "pending"]),
            )
            .order_by(desc(Conversation.last_activity_at))
            .limit(1)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # 更新最后活动时间
            existing.last_activity_at = datetime.now(timezone.utc)
            await self.db.flush()
            return existing

        # 创建新会话
        return await self.create_conversation(
            inbox_id=inbox_id,
            contact_id=contact_id,
            contact_inbox_id=contact_inbox_id,
            title=title,
        )

    async def update_conversation(
        self, conversation_id: str, data: ConversationUpdate
    ) -> Conversation | None:
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(conversation, key, value)

        if "status" in update_data and update_data["status"] == "resolved":
            conversation.resolved_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation

    async def resolve_conversation(self, conversation_id: str) -> Conversation | None:
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return None
        conversation.status = "resolved"
        conversation.resolved_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation

    async def snooze_conversation(
        self, conversation_id: str, until: datetime | None = None
    ) -> Conversation | None:
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return None
        conversation.status = "snoozed"
        conversation.snoozed_until = until
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation

    async def assign_agent(
        self, conversation_id: str, agent_id: str
    ) -> Conversation | None:
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return None
        conversation.assigned_agent_id = agent_id
        conversation.waiting_since = None
        if conversation.first_reply_created_at is None:
            conversation.first_reply_created_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation

    async def auto_assign(self, conversation: Conversation) -> Conversation:
        """自动分配 Agent（创建会话时调用）"""
        assignment_svc = AssignmentService(self.db)
        agent = await assignment_svc.assign_agent(
            conversation, algorithm="round_robin"
        )
        if agent:
            conversation.assigned_agent_id = agent.id
            conversation.waiting_since = None
        else:
            conversation.waiting_since = datetime.now(timezone.utc)
        await self.db.flush()
        return conversation

    async def get_messages(
        self, conversation_id: str, page: int = 1, page_size: int = 50
    ) -> tuple[list[Message], int]:
        """获取会话消息历史"""
        count_q = select(func.count()).select_from(Message).where(
            Message.conversation_id == conversation_id
        )
        total = (await self.db.execute(count_q)).scalar() or 0

        items_q = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(items_q)
        return list(result.scalars().all()), total
