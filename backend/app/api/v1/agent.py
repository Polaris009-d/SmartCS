"""
Agent API — 订单查询、物流查询、退款、审计日志
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.agent_operation_log import AgentOperationLog
from app.schemas.agent import (
    OrderQueryRequest, OrderQueryResponse,
    LogisticsQueryRequest, LogisticsQueryResponse,
    AgentLogResponse,
)
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.post("/agent/order/query", response_model=OrderQueryResponse)
async def query_order(
    data: OrderQueryRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """按订单号查询"""
    from app.agents.tools.order_tools import OrderTool
    tool = OrderTool(db)
    order = await tool.query_by_order_no(data.order_no)
    if not order:
        raise HTTPException(status_code=404, detail=f"订单 {data.order_no} 不存在")
    return OrderQueryResponse(**order)


@router.get("/agent/order/query-by-contact")
async def query_orders_by_contact(
    contact_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """按联系人ID查询所有订单"""
    from app.agents.tools.order_tools import OrderTool
    tool = OrderTool(db)
    orders = await tool.query_by_contact(contact_id)
    return {"orders": orders, "total": len(orders)}


@router.post("/agent/logistics/query", response_model=LogisticsQueryResponse)
async def query_logistics(
    data: LogisticsQueryRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """查询物流"""
    from app.agents.tools.logistics_tools import LogisticsTool
    tool = LogisticsTool(db)
    result = await tool.track_by_order_no(data.order_no)
    if not result:
        raise HTTPException(status_code=404, detail=f"订单 {data.order_no} 不存在")
    return LogisticsQueryResponse(**result)


@router.post("/agent/refund")
async def process_refund(
    data: OrderQueryRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """自动退款（经安全规则校验）"""
    from app.agents.safety_engine import SafetyEngine
    from app.agents.tools.refund_tools import RefundTool
    from app.agents.tools.order_tools import OrderTool
    from app.agents.refund_agent import RefundAgent

    safety = SafetyEngine()
    refund_tool = RefundTool(db)
    order_tool = OrderTool(db)
    agent = RefundAgent(safety, refund_tool, order_tool)

    result = await agent.execute(
        conversation_id="",
        user_message=f"退款 {data.order_no}",
        context={},
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return {
        "success": True,
        "message": result.message,
        "data": result.data,
        "safety": {
            "allowed": result.safety_result.allowed if result.safety_result else False,
            "risk_level": result.safety_result.risk_level if result.safety_result else "unknown",
        },
    }


@router.get("/agent/logs", response_model=PaginatedResponse[AgentLogResponse])
async def list_agent_logs(
    conversation_id: str | None = Query(default=None),
    agent_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """查询 Agent 操作审计日志"""
    conditions = []
    if conversation_id:
        conditions.append(AgentOperationLog.conversation_id == conversation_id)
    if agent_type:
        conditions.append(AgentOperationLog.agent_type == agent_type)
    if status:
        conditions.append(AgentOperationLog.status == status)

    where_clause = (*conditions,) if conditions else (True,)

    count_q = select(func.count()).select_from(AgentOperationLog).where(*where_clause)
    total = (await db.execute(count_q)).scalar() or 0

    items_q = (
        select(AgentOperationLog)
        .where(*where_clause)
        .order_by(desc(AgentOperationLog.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(items_q)
    logs = result.scalars().all()

    return PaginatedResponse.from_items(
        items=[AgentLogResponse.model_validate(log) for log in logs],
        total=total, page=page, page_size=page_size,
    )
