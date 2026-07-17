"""
订单查询 Agent
"""
from app.agents.base import BaseAgent, AgentResult
from app.agents.safety_engine import SafetyEngine
from app.agents.router import extract_order_no
from app.agents.tools.order_tools import OrderTool


ORDER_KEYWORDS = ["订单", "查订单", "我的订单", "订单状态", "买了什么", "买的东西"]


class OrderAgent(BaseAgent):
    def __init__(self, safety_engine: SafetyEngine, order_tool: OrderTool):
        super().__init__(safety_engine)
        self.order_tool = order_tool

    @property
    def agent_type(self) -> str: return "order_agent"

    def match(self, user_message: str) -> bool:
        return any(kw in user_message for kw in ORDER_KEYWORDS)

    async def execute(self, conversation_id: str, user_message: str, context: dict | None = None) -> AgentResult:
        ctx = context or {}
        order_no = extract_order_no(user_message)
        contact_id = ctx.get("contact_id")

        if order_no:
            return await self._run_with_safety(
                action="order.query", params={"order_no": order_no},
                conversation_id=conversation_id, business_context=ctx,
                execute_fn=lambda p, c: self._query_by_order(p["order_no"]),
            )

        if contact_id:
            orders = await self.order_tool.query_by_contact(contact_id)
            return AgentResult(
                success=True, action="order.list",
                data={"orders": orders},
                message=f"请选择要查询的订单（共{len(orders)}个）",
            )

        return AgentResult(success=False, action="order.query", message="暂无订单信息")

    async def _query_by_order(self, order_no: str) -> dict | None:
        return await self.order_tool.query_by_order_no(order_no)
