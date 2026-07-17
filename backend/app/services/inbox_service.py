"""
渠道服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.inbox import Inbox
from app.schemas.inbox import InboxCreate, InboxUpdate


class InboxService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_inboxes(self) -> list[Inbox]:
        result = await self.db.execute(
            select(Inbox).order_by(Inbox.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_inbox(self, inbox_id: str) -> Inbox | None:
        result = await self.db.execute(
            select(Inbox).where(Inbox.id == inbox_id)
        )
        return result.scalar_one_or_none()

    async def create_inbox(self, data: InboxCreate) -> Inbox:
        inbox = Inbox(
            name=data.name,
            channel_type=data.channel_type,
            channel_config=data.channel_config,
            auto_assignment_enabled=data.auto_assignment_enabled,
            assignment_algorithm=data.assignment_algorithm,
            greeting_message=data.greeting_message,
        )
        self.db.add(inbox)
        await self.db.flush()
        return inbox

    async def update_inbox(self, inbox_id: str, data: InboxUpdate) -> Inbox | None:
        inbox = await self.get_inbox(inbox_id)
        if not inbox:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(inbox, key, value)
        await self.db.flush()
        return inbox

    async def delete_inbox(self, inbox_id: str) -> bool:
        inbox = await self.get_inbox(inbox_id)
        if not inbox:
            return False
        await self.db.delete(inbox)
        await self.db.flush()
        return True
