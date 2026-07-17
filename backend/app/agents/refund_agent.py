"""
退款 Agent — 自动退款 + 安全规则校验 + 风控升级
"""
import re
from app.agents.base import BaseAgent, AgentResult
from app.agents.safety_engine import SafetyEngine
from app.agents.tools.refund_tools import RefundTool
from app.agents.tools.order_tools import OrderTool

REFUND_KEYWORDS = ["退款", "退钱", "申请退款", "不想要了", "取消订单", "退单"]


class RefundAgent(BaseAgent):
    """退款 Agent — 多层安全校验，符合条件的自动退款，否则转人工"""

    def __init__(self, safety_engine: SafetyEngine, refund_tool: RefundTool, order_tool: OrderTool):
        super().__init__(safety_engine)
        self.refund_tool = refund_tool
        self.order_tool = order_tool

    @property
    def agent_type(self) -> str:
        return "refund_agent"

    def match(self, user_message: str) -> bool:
        return any(kw in user_message for kw in REFUND_KEYWORDS)

    async def execute(
        self,
        conversation_id: str,
        user_message: str,
        context: dict | None = None,
    ) -> AgentResult:
        ctx = context or {}
        order_no = self._extract_order_no(user_message)

        if not order_no:
            # 没有指定订单号 → 返回可选订单列表，高亮上次查询的
            contact_id = ctx.get("contact_id")
            if contact_id:
                orders = await self.order_tool.query_by_contact(contact_id)
                if orders:
                    return AgentResult(
                        success=True, action="refund.list",
                        data={
                            "orders": orders,
                            "last_order_no": ctx.get("last_order_no"),
                        },
                        message="请选择要退款的订单",
                    )
            return AgentResult(
                success=False, action="refund.execute",
                message="请提供您的订单号，我帮您申请退款。例如：ORD-20260714001",
            )

        # 获取订单上下文
        order_ctx = await self.refund_tool.get_order_context(order_no)
        if not order_ctx:
            return AgentResult(
                success=False, action="refund.execute",
                message=f"订单 {order_no} 不存在，请核实订单号后重试。",
            )

        amount = self._extract_amount(user_message) or order_ctx["order_amount"]
        reason = user_message[:200]

        return await self._run_with_safety(
            action="refund.execute",
            params={"order_no": order_no, "amount": amount, "reason": reason},
            conversation_id=conversation_id,
            business_context=order_ctx,
            execute_fn=lambda p, c: self.refund_tool.execute_refund(
                order_no=p["order_no"], amount=p["amount"], reason=p.get("reason", "")
            ),
        )

    def _extract_order_no(self, text: str) -> str | None:
        match = re.search(r'(ORD-\d+)', text, re.IGNORECASE)
        if match: return match.group(1).upper()
        match = re.search(r'\b(\d{10,20})\b', text)
        return match.group(1) if match else None

    def _extract_amount(self, text: str) -> float | None:
        match = re.search(r'(\d+\.?\d*)\s*元', text)
        if match: return float(match.group(1))
        match = re.search(r'¥\s*(\d+\.?\d*)', text)
        return float(match.group(1)) if match else None
