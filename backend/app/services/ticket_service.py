"""
工单服务
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.ticket import Ticket
from app.services.sse_manager import sse_manager


class TicketService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_tickets(
        self, status: str | None = None, ticket_type: str | None = None,
        assigned_user_id: str | None = None, page: int = 1, page_size: int = 20,
    ) -> tuple[list[Ticket], int]:
        conditions = []
        if status:
            conditions.append(Ticket.status == status)
        if ticket_type:
            conditions.append(Ticket.ticket_type == ticket_type)
        if assigned_user_id:
            conditions.append(Ticket.assigned_user_id == assigned_user_id)
        where_clause = (*conditions,) if conditions else (True,)

        count_q = select(func.count()).select_from(Ticket).where(*where_clause)
        total = (await self.db.execute(count_q)).scalar() or 0

        items_q = (
            select(Ticket).where(*where_clause)
            .order_by(desc(Ticket.created_at))
            .offset((page - 1) * page_size).limit(page_size)
        )
        result = await self.db.execute(items_q)
        return list(result.scalars().all()), total

    async def get_ticket(self, ticket_id: str) -> Ticket | None:
        result = await self.db.execute(select(Ticket).where(Ticket.id == ticket_id))
        return result.scalar_one_or_none()

    async def create_ticket(
        self, ticket_type: str, subject: str, customer_id: str,
        conversation_id: str | None = None, order_id: str | None = None,
        priority: str = "normal", description: str | None = None,
    ) -> Ticket:
        now = datetime.now(timezone.utc)
        ticket = Ticket(
            conversation_id=conversation_id,
            order_id=order_id,
            customer_id=customer_id,
            ticket_type=ticket_type,
            priority=priority,
            status="open",
            subject=subject,
            description=description,
            created_at=now,
            updated_at=now,
        )
        self.db.add(ticket)
        await self.db.flush()

        # SSE 通知所有在线客服
        await sse_manager.publish_agent_broadcast("ticket.created", {
            "id": ticket.id,
            "ticket_type": ticket_type,
            "subject": subject,
            "priority": priority,
        })
        return ticket

    async def update_ticket(self, ticket_id: str, **kwargs) -> Ticket | None:
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return None
        for key, value in kwargs.items():
            if hasattr(ticket, key):
                setattr(ticket, key, value)
        now = datetime.now(timezone.utc)
        if kwargs.get("status") == "resolved" and not ticket.resolved_at:
            ticket.resolved_at = now
        if kwargs.get("status") == "closed" and not ticket.closed_at:
            ticket.closed_at = now
        ticket.updated_at = now
        await self.db.flush()
        return ticket

    async def assign_ticket(self, ticket_id: str, user_id: str) -> Ticket | None:
        return await self.update_ticket(
            ticket_id, assigned_user_id=user_id, status="in_progress"
        )
