"""
物流查询 Agent
"""
from app.agents.base import BaseAgent, AgentResult
from app.agents.safety_engine import SafetyEngine
from app.agents.router import extract_order_no
from app.agents.tools.logistics_tools import LogisticsTool
from app.agents.tools.order_tools import OrderTool


LOGISTICS_KEYWORDS = ["物流", "快递", "到哪了", "发货", "运输", "包裹", "跟踪", "快递单号"]


class LogisticsAgent(BaseAgent):
    def __init__(self, safety_engine: SafetyEngine, logistics_tool: LogisticsTool, order_tool: OrderTool):
        super().__init__(safety_engine)
        self.logistics_tool = logistics_tool
        self.order_tool = order_tool

    @property
    def agent_type(self) -> str: return "logistics_agent"

    def match(self, user_message: str) -> bool:
        return any(kw in user_message for kw in LOGISTICS_KEYWORDS)

    async def execute(self, conversation_id: str, user_message: str, context: dict | None = None) -> AgentResult:
        ctx = context or {}
        order_no = extract_order_no(user_message)
        contact_id = ctx.get("contact_id")

        if order_no:
            return await self._run_with_safety(
                action="logistics.track", params={"order_no": order_no},
                conversation_id=conversation_id, business_context=ctx,
                execute_fn=lambda p, c: self.logistics_tool.track_by_order_no(p["order_no"]),
            )

        if contact_id:
            orders = await self.order_tool.query_by_contact(contact_id)
            shipped = [o for o in orders if o.get("logistics_no")]
            if shipped:
                return AgentResult(
                    success=True, action="logistics.list",
                    data={"orders": shipped},
                    message=f"请选择要查物流的订单（共{len(shipped)}个已发货）",
                )
            return AgentResult(success=False, action="logistics.track", message="当前没有已发货的订单")

        return AgentResult(success=False, action="logistics.track", message="暂无物流信息")
