"""
绩效看板 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/dashboard/performance")
async def get_performance(
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """客服绩效数据 — 会话量、AI处理率、消息分布、Agent操作统计"""
    svc = DashboardService(db)
    return await svc.get_stats(days=days)
