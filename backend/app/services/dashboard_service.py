"""
绩效看板服务 — 会话量、AI处理率、响应时长、满意度统计
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.conversation import Conversation
from app.models.message import Message


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self, days: int = 7) -> dict:
        """获取指定天数范围内的聚合统计数据"""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # 总会话数（时间范围内）
        total_conv_q = select(func.count()).select_from(Conversation).where(
            Conversation.created_at >= since
        )
        total_conversations = (await self.db.execute(total_conv_q)).scalar() or 0

        # 各状态会话数
        status_q = (
            select(Conversation.status, func.count())
            .where(Conversation.created_at >= since)
            .group_by(Conversation.status)
        )
        status_result = await self.db.execute(status_q)
        status_counts = {row[0]: row[1] for row in status_result}

        # AI 处理会话数
        ai_q = select(func.count()).select_from(Conversation).where(
            Conversation.is_ai_handling == True,
            Conversation.created_at >= since,
        )
        ai_handled = (await self.db.execute(ai_q)).scalar() or 0

        # 总会话消息数（时间范围内）
        total_msg_q = select(func.count()).select_from(Message).where(
            Message.created_at >= since
        )
        total_messages = (await self.db.execute(total_msg_q)).scalar() or 0

        # AI 消息数
        ai_msg_q = select(func.count()).select_from(Message).where(
            Message.sender_type == "ai",
            Message.created_at >= since,
        )
        ai_messages = (await self.db.execute(ai_msg_q)).scalar() or 0

        # 各消息类型分布
        type_q = (
            select(Message.sender_type, func.count())
            .where(Message.created_at >= since)
            .group_by(Message.sender_type)
        )
        type_result = await self.db.execute(type_q)
        sender_distribution = {row[0]: row[1] for row in type_result}

        # Agent 操作统计
        from app.models.agent_operation_log import AgentOperationLog
        agent_q = (
            select(
                AgentOperationLog.agent_type,
                AgentOperationLog.status,
                func.count(),
            )
            .where(AgentOperationLog.created_at >= since)
            .group_by(AgentOperationLog.agent_type, AgentOperationLog.status)
        )
        agent_result = await self.db.execute(agent_q)
        agent_stats = {}
        for row in agent_result:
            atype = row[0]
            if atype not in agent_stats:
                agent_stats[atype] = {"success": 0, "rejected": 0, "error": 0}
            agent_stats[atype][row[1]] = row[2]

        ai_handling_rate = round(ai_handled / total_conversations * 100, 1) if total_conversations > 0 else 0

        return {
            "period_days": days,
            "conversations": {
                "total": total_conversations,
                "by_status": status_counts,
                "ai_handled": ai_handled,
                "ai_handling_rate": ai_handling_rate,
                "human_handled": total_conversations - ai_handled,
            },
            "messages": {
                "total": total_messages,
                "ai_messages": ai_messages,
                "by_sender_type": sender_distribution,
            },
            "agent_operations": agent_stats,
            "avg_ai_confidence": await self._avg_ai_confidence(since),
        }

    async def _avg_ai_confidence(self, since: datetime) -> float:
        q = select(func.avg(Message.ai_confidence)).where(
            Message.sender_type == "ai",
            Message.ai_confidence.is_not(None),
            Message.created_at >= since,
        )
        result = await self.db.execute(q)
        avg = result.scalar()
        return round(float(avg), 3) if avg else 0.0
