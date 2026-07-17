"""
退款 Tool — 执行退款操作 + 风控检查
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.order import Order
from app.models.contact import Contact
from app.models.refund_record import RefundRecord
from app.core.config import settings


class RefundTool:
    """退款执行工具"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_order_context(self, order_no: str) -> dict | None:
        """获取订单上下文（状态、金额、客户信誉、当日退款次数）"""
        result = await self.db.execute(
            select(Order).where(Order.order_no == order_no)
        )
        order = result.scalar_one_or_none()
        if not order:
            return None

        # 客户信誉
        contact = await self.db.get(Contact, order.contact_id)
        reputation = contact.reputation_score if contact else 1.0

        # 当日退款次数
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        count_result = await self.db.execute(
            select(func.count()).select_from(RefundRecord).where(
                RefundRecord.customer_id == order.contact_id,
                RefundRecord.created_at >= today_start,
                RefundRecord.status.in_(["approved", "processed"]),
            )
        )
        daily_refund_count = count_result.scalar() or 0

        return {
            "order_status": order.status,
            "order_amount": float(order.total_amount),
            "customer_reputation": reputation,
            "daily_refund_count": daily_refund_count,
            "contact_id": order.contact_id,
            "order_id": order.id,
        }

    async def execute_refund(self, order_no: str, amount: float, reason: str) -> dict:
        """执行退款：更新订单状态 + 创建退款记录"""
        # 查询订单
        result = await self.db.execute(
            select(Order).where(Order.order_no == order_no)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError(f"订单 {order_no} 不存在")

        now = datetime.now(timezone.utc)

        # Mock: 调用外部支付API进行退款
        external_refund_id = f"RF-{order_no}-{now.strftime('%Y%m%d%H%M%S')}"

        # 创建退款记录
        refund = RefundRecord(
            order_id=order.id,
            customer_id=order.contact_id,
            amount=amount,
            reason=reason,
            status="processed",
            processed_by="ai",
            approval_rule=f"auto_refund: amount<={settings.AUTO_REFUND_MAX_AMOUNT}",
            external_refund_id=external_refund_id,
            created_at=now,
            processed_at=now,
        )
        self.db.add(refund)

        # 更新订单状态
        order.status = "refunding"
        order.payment_status = "refunded"
        order.updated_at = now

        await self.db.flush()

        return {
            "refund_id": refund.id,
            "external_refund_id": external_refund_id,
            "order_no": order_no,
            "amount": amount,
            "status": "processed",
            "estimated_arrival": "1-3 个工作日到账",
        }
