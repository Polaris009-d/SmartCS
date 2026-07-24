"""
情感分析服务 — LLM 情绪打分 + 自动预警
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.llm.base import ChatMessage
from app.llm.factory import get_llm_provider
from app.models.sentiment_alert import SentimentAlert
from app.core.config import settings

SENTIMENT_PROMPT = """分析客服消息的情绪，score越高=越不满。
0.0~0.29=满意 0.3~0.69=中性 0.7~0.89=不满 0.9~1.0=非常不满
请根据消息的实际内容客观评分，不要使用固定值。

客户消息：{message}

只返回JSON（sentiment必须是 positive/neutral/negative/very_negative 之一）：{{}}"""


class SentimentService:
    """情感分析 — 对客户消息进行情绪打分，触发预警和升级"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_provider()

    async def analyze(self, message: str) -> dict:
        """分析单条消息的情感"""
        try:
            prompt = SENTIMENT_PROMPT.format(message=message[:500])
            resp = await self.llm.chat(
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.1,
                max_tokens=200,
            )
            import json, re
            text = resp.content.strip()
            # 去掉 markdown 代码块包裹
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            # 尝试提取第一个 JSON 对象（支持多行）
            m = re.search(r'\{[^{}]*\}', text)
            if m:
                result = json.loads(m.group())
                return {
                    "sentiment": result.get("sentiment", "neutral"),
                    "score": float(result.get("score", 0.5)),
                    "reason": result.get("reason", ""),
                }
            raise ValueError("no JSON found")
        except Exception as e:
            print(f"[Sentiment] LLM failed: {e}, falling back to keywords for: {message[:50]}")
            return self._fallback_analyze(message)

    def _fallback_analyze(self, message: str) -> dict:
        """关键词降级情感分析"""
        negative_words = ["投诉", "差劲", "垃圾", "骗子", "退款", "退货", "太差", "坑", "气死", "坑人", "失望"]
        very_negative_words = ["举报", "投诉到底", "维权", "315", "客服态度差"]

        score = 0.3  # neutral baseline
        for w in very_negative_words:
            if w in message:
                score = 0.9
                break
        for w in negative_words:
            if w in message and score < 0.7:
                score = 0.7

        if score >= 0.8:
            sentiment = "very_negative"
        elif score >= 0.7:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {"sentiment": sentiment, "score": score, "reason": "关键词匹配"}

    async def check_and_alert(
        self,
        conversation_id: str,
        message_id: str,
        customer_id: str,
        message: str,
    ) -> SentimentAlert | None:
        """分析消息并在满足阈值时创建预警"""
        result = await self.analyze(message)
        score = result["score"]

        if score < settings.SENTIMENT_THRESHOLD:
            return None  # 未触发预警

        alert_level = "warning"
        if score >= settings.SENTIMENT_CRITICAL_THRESHOLD:
            alert_level = "critical"

        now = datetime.now(timezone.utc)
        alert = SentimentAlert(
            conversation_id=conversation_id,
            message_id=message_id,
            customer_id=customer_id,
            sentiment_label=result["sentiment"],
            sentiment_score=score,
            alert_level=alert_level,
            is_escalated=alert_level == "critical",
            created_at=now,
        )
        self.db.add(alert)

        # 自动升级：创建工单
        if alert_level == "critical":
            from app.models.ticket import Ticket
            import uuid
            ticket = Ticket(
                conversation_id=conversation_id,
                customer_id=customer_id,
                ticket_type="escalation",
                subject=f"情感预警自动升级 - {result['sentiment']} ({score:.0%})",
                description=f"客户消息触发严重情感预警：{result.get('reason', '')}\n消息内容：{message[:200]}",
                priority="urgent",
                status="open",
            )
            self.db.add(ticket)
            await self.db.flush()
            alert.escalation_ticket_id = ticket.id

        await self.db.flush()
        return alert
