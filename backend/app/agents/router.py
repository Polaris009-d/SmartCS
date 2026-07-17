"""
Agent 路由器 — 意图识别与 Agent 路由
根据用户消息内容，路由到对应的 Agent 执行
"""
import re
from app.agents.base import BaseAgent, AgentResult


class AgentRouter:
    """
    意图路由器。
    MVP 阶段使用关键词 + 正则匹配实现意图识别。
    后续可升级为 LLM 意图分类。
    """

    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent):
        """注册 Agent"""
        self._agents[agent.agent_type] = agent

    def route(self, user_message: str) -> BaseAgent | None:
        """
        根据用户消息匹配最合适的 Agent。
        遍历所有注册 Agent 调用其 match() 方法。
        """
        for agent in self._agents.values():
            if agent.match(user_message):
                return agent
        return None

    async def execute(
        self,
        user_message: str,
        conversation_id: str,
        context: dict | None = None,
    ) -> AgentResult | None:
        """
        路由并执行 Agent。如果无匹配返回 None。
        """
        agent = self.route(user_message)
        if agent is None:
            return None
        return await agent.execute(conversation_id, user_message, context)

    def get_agent(self, agent_type: str) -> BaseAgent | None:
        return self._agents.get(agent_type)


def extract_order_no(text: str) -> str | None:
    """从用户消息中提取订单号"""
    # 匹配 ORD- 开头的订单号
    match = re.search(r'(ORD-\d+)', text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    # 匹配纯数字长串
    match = re.search(r'\b(\d{10,20})\b', text)
    if match:
        return match.group(1)
    return None
