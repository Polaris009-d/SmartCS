"""
工单 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.ticket_service import TicketService
from app.schemas.common import PaginatedResponse

router = APIRouter()


def _ticket_to_dict(t) -> dict:
    return {
        "id": t.id, "conversation_id": t.conversation_id, "order_id": t.order_id,
        "customer_id": t.customer_id, "assigned_user_id": t.assigned_user_id,
        "ticket_type": t.ticket_type, "priority": t.priority, "status": t.status,
        "subject": t.subject, "description": t.description, "resolution": t.resolution,
        "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
        "closed_at": t.closed_at.isoformat() if t.closed_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else "",
        "updated_at": t.updated_at.isoformat() if t.updated_at else "",
    }


@router.get("/tickets")
async def list_tickets(
    status: str | None = Query(default=None),
    ticket_type: str | None = Query(default=None),
    assigned_user_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    svc = TicketService(db)
    tickets, total = await svc.list_tickets(
        status=status, ticket_type=ticket_type,
        assigned_user_id=assigned_user_id, page=page, page_size=page_size,
    )
    return PaginatedResponse.from_items(
        items=[_ticket_to_dict(t) for t in tickets],
        total=total, page=page, page_size=page_size,
    )


@router.post("/tickets")
async def create_ticket(
    ticket_type: str = Body(...),
    subject: str = Body(...),
    customer_id: str = Body(...),
    conversation_id: str | None = Body(default=None),
    order_id: str | None = Body(default=None),
    priority: str = Body(default="normal"),
    description: str | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    svc = TicketService(db)
    ticket = await svc.create_ticket(
        ticket_type=ticket_type, subject=subject, customer_id=customer_id,
        conversation_id=conversation_id, order_id=order_id,
        priority=priority, description=description,
    )
    return _ticket_to_dict(ticket)


@router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    svc = TicketService(db)
    ticket = await svc.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    return _ticket_to_dict(ticket)


@router.patch("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = TicketService(db)
    ticket = await svc.update_ticket(ticket_id, **data)
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    return _ticket_to_dict(ticket)


@router.post("/tickets/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    user_id: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    svc = TicketService(db)
    ticket = await svc.assign_ticket(ticket_id, user_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    return _ticket_to_dict(ticket)
