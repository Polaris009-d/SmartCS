"""
订单查询 Tool — 供 Agent 使用的业务工具
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order


class OrderTool:
    """订单查询工具"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def query_by_order_no(self, order_no: str) -> dict | None:
        """根据订单号查询订单"""
        result = await self.db.execute(
            select(Order).where(Order.order_no == order_no)
        )
        order = result.scalar_one_or_none()
        if not order:
            return None
        return {
            "order_no": order.order_no,
            "product_name": order.product_name,
            "quantity": order.quantity,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "payment_status": order.payment_status,
            "logistics_no": order.logistics_no,
            "logistics_status": order.logistics_status,
            "shipping_address": order.shipping_address,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }

    async def query_by_contact(self, contact_id: str) -> list[dict]:
        """根据联系人 ID 查询所有订单"""
        result = await self.db.execute(
            select(Order)
            .where(Order.contact_id == contact_id)
            .order_by(Order.created_at.desc())
            .limit(10)
        )
        orders = result.scalars().all()
        return [
            {
                "order_no": o.order_no,
                "product_name": o.product_name,
                "quantity": o.quantity,
                "total_amount": float(o.total_amount),
                "status": o.status,
                "payment_status": o.payment_status,
                "logistics_no": o.logistics_no,
                "logistics_status": o.logistics_status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ]
