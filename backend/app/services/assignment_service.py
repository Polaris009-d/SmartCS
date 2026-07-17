"""
会话分配服务 — 参考 Chatwoot Assignment v2
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User
from app.models.conversation import Conversation


class AssignmentService:
    """
    自动分配策略：
      - round_robin: Redis 维护指针（简化实现：按最近分配时间+会话数）
      - balanced: 选择当前活跃会话数最少的在线 Agent
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_available_agents(self) -> list[User]:
        """获取在线且未达容量上限的 Agent 列表"""
        result = await self.db.execute(
            select(User).where(
                User.is_active == True,
                User.availability.in_(["online"]),
            )
        )
        agents = list(result.scalars().all())

        # 过滤超出并发上限的 Agent
        available = []
        for agent in agents:
            active_count = await self._count_active_conversations(agent.id)
            if active_count < agent.max_concurrent:
                available.append(agent)
        return available

    async def assign_agent(
        self, conversation: Conversation, algorithm: str = "round_robin"
    ) -> User | None:
        """为会话分配最合适的 Agent"""
        agents = await self.get_available_agents()
        if not agents:
            return None

        if algorithm == "balanced":
            return await self._balanced_assign(agents)

        # 默认 round_robin
        return await self._round_robin_assign(agents)

    async def _round_robin_assign(self, agents: list[User]) -> User:
        """轮询分配：选择活跃会话数最少的 Agent"""
        # 与 balanced 在 MVP 阶段逻辑相同
        return await self._balanced_assign(agents)

    async def _balanced_assign(self, agents: list[User]) -> User:
        """均衡分配：选择活跃会话数最少的 Agent"""
        min_agent = agents[0]
        min_count = await self._count_active_conversations(min_agent.id)

        for agent in agents[1:]:
            count = await self._count_active_conversations(agent.id)
            if count < min_count:
                min_count = count
                min_agent = agent

        return min_agent

    async def _count_active_conversations(self, agent_id: str) -> int:
        """统计某 Agent 当前活跃（open）会话数"""
        result = await self.db.execute(
            select(func.count()).select_from(Conversation).where(
                Conversation.assigned_agent_id == agent_id,
                Conversation.status == "open",
            )
        )
        return result.scalar() or 0
