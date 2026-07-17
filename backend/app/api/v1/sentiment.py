"""
情感预警 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.sentiment_alert import SentimentAlert
from app.schemas.common import PaginatedResponse

router = APIRouter()


class SentimentAlertResponse:
    """简化响应模型"""
    pass


@router.get("/sentiment/alerts")
async def list_alerts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    alert_level: str | None = Query(default=None),
    is_escalated: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """情感预警列表"""
    from sqlalchemy import func

    conditions = []
    if alert_level:
        conditions.append(SentimentAlert.alert_level == alert_level)
    if is_escalated is not None:
        conditions.append(SentimentAlert.is_escalated == is_escalated)

    where_clause = (*conditions,) if conditions else (True,)
    count_q = select(func.count()).select_from(SentimentAlert).where(*where_clause)
    total = (await db.execute(count_q)).scalar() or 0

    items_q = (
        select(SentimentAlert)
        .where(*where_clause)
        .order_by(desc(SentimentAlert.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(items_q)
    alerts = result.scalars().all()

    return PaginatedResponse.from_items(
        items=[{
            "id": a.id,
            "conversation_id": a.conversation_id,
            "message_id": a.message_id,
            "customer_id": a.customer_id,
            "sentiment_label": a.sentiment_label,
            "sentiment_score": a.sentiment_score,
            "alert_level": a.alert_level,
            "is_escalated": a.is_escalated,
            "handled_by": a.handled_by,
            "handled_at": a.handled_at.isoformat() if a.handled_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        } for a in alerts],
        total=total, page=page, page_size=page_size,
    )
