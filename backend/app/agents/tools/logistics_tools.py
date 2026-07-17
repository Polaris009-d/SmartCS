"""
物流查询 Tool — 供 Agent 使用的业务工具
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order


class LogisticsTool:
    """物流查询工具"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def track_by_order_no(self, order_no: str) -> dict | None:
        """根据订单号查询物流状态"""
        result = await self.db.execute(
            select(Order).where(Order.order_no == order_no)
        )
        order = result.scalar_one_or_none()
        if not order:
            return None

        if not order.logistics_no:
            return {
                "order_no": order.order_no,
                "status": order.status,
                "message": "订单尚未发货，暂无物流信息",
                "logistics_no": None,
                "logistics_status": None,
                "shipped_at": None,
            }

        # Mock 物流轨迹
        tracking_details = _mock_tracking(order.logistics_no, order.logistics_status or "")

        return {
            "order_no": order.order_no,
            "logistics_no": order.logistics_no,
            "logistics_status": order.logistics_status,
            "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
            "tracking_details": tracking_details,
        }


def _mock_tracking(logistics_no: str, current_status: str) -> str:
    """Mock 物流轨迹数据（实际应调用物流API）"""
    return f"""
【快递单号】{logistics_no}
2026-07-14 08:30  快件在【北京转运中心】完成分拣，准备发往【上海】
2026-07-13 20:15  快件到达【北京转运中心】
2026-07-13 15:00  【北京市朝阳区网点】已揽收
2026-07-13 14:30  商家已发货，等待快递员揽收
当前状态: {current_status}
"""
