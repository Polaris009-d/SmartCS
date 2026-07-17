"""
Pydantic 安全规则引擎 — 5 层安全模型的核心实现
"""
from pydantic import BaseModel, Field
from app.core.config import settings
from enum import Enum


class SafetyDecision(str, Enum):
    PASS = "pass"
    BLOCK = "block"
    ESCALATE = "escalate"


class SafetyResult(BaseModel):
    allowed: bool
    decision: SafetyDecision
    reason: str | None = None
    risk_level: str = "low"


class RefundParams(BaseModel):
    """退款参数校验"""
    order_no: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    reason: str = Field(default="", max_length=500)


class OrderQueryParams(BaseModel):
    order_no: str = Field(..., min_length=1, max_length=100)


class LogisticsQueryParams(BaseModel):
    order_no: str = Field(..., min_length=1, max_length=100)


_STATUS_CN = {
    "pending": "待付款", "paid": "已付款", "shipped": "已发货",
    "delivered": "已签收", "cancelled": "已取消", "refunding": "退款中",
}


class SafetyEngine:
    """
    安全规则引擎 — Pydantic 参数校验 + 业务规则校验。
    LLM 只负责意图识别和参数提取，实际执行由此引擎控制。
    """

    def validate(self, action: str, params: dict, context: dict | None = None) -> SafetyResult:
        ctx = context or {}

        if action in ("order.list", "refund.list", "logistics.list"):
            return SafetyResult(allowed=True, decision=SafetyDecision.PASS, risk_level="low")
        elif action == "order.query":
            return self._validate_order_query(params)
        elif action in ("logistics.track", "logistics.query"):
            return self._validate_logistics_query(params)
        elif action == "refund.execute":
            return self._validate_refund(params, ctx)
        else:
            return SafetyResult(allowed=False, decision=SafetyDecision.BLOCK, reason=f"未知操作类型: {action}")

    def _validate_order_query(self, params: dict) -> SafetyResult:
        try:
            OrderQueryParams(**params)
        except Exception:
            return SafetyResult(allowed=False, decision=SafetyDecision.BLOCK, reason="订单号格式不正确")
        return SafetyResult(allowed=True, decision=SafetyDecision.PASS, risk_level="low")

    def _validate_logistics_query(self, params: dict) -> SafetyResult:
        try:
            LogisticsQueryParams(**params)
        except Exception:
            return SafetyResult(allowed=False, decision=SafetyDecision.BLOCK, reason="订单号格式不正确")
        return SafetyResult(allowed=True, decision=SafetyDecision.PASS, risk_level="low")

    def _validate_refund(self, params: dict, ctx: dict) -> SafetyResult:
        try:
            validated = RefundParams(**params)
        except Exception:
            return SafetyResult(allowed=False, decision=SafetyDecision.BLOCK, reason="退款参数不完整，请检查订单号和金额")

        # 订单状态检查
        order_status = ctx.get("order_status", "")
        status_cn = _STATUS_CN.get(order_status, order_status)
        if order_status in ("shipped", "delivered"):
            return SafetyResult(
                allowed=False, decision=SafetyDecision.ESCALATE,
                reason=f"订单状态为「{status_cn}」，无法自动退款，已转人工处理",
                risk_level="medium",
            )
        if order_status in ("refunding", "cancelled"):
            return SafetyResult(
                allowed=False, decision=SafetyDecision.BLOCK,
                reason=f"订单状态为「{status_cn}」，无法重复退款",
                risk_level="high",
            )

        # 金额检查
        if validated.amount > settings.AUTO_REFUND_MAX_AMOUNT:
            return SafetyResult(
                allowed=False, decision=SafetyDecision.ESCALATE,
                reason=f"退款金额 ¥{validated.amount:.0f} 超过自动退款上限 ¥{settings.AUTO_REFUND_MAX_AMOUNT:.0f}，已转人工处理",
                risk_level="high",
            )

        # 信誉检查
        reputation = ctx.get("customer_reputation", 1.0)
        if reputation < 0.5:
            return SafetyResult(
                allowed=False, decision=SafetyDecision.ESCALATE,
                reason=f"用户信誉分过低（{reputation:.0%}），已转人工审核",
                risk_level="high",
            )

        # 频次检查
        daily_count = ctx.get("daily_refund_count", 0)
        if daily_count >= settings.AUTO_REFUND_MAX_DAILY:
            return SafetyResult(
                allowed=False, decision=SafetyDecision.ESCALATE,
                reason=f"用户今日退款次数已达 {settings.AUTO_REFUND_MAX_DAILY} 次上限，已转人工审核",
                risk_level="medium",
            )

        return SafetyResult(allowed=True, decision=SafetyDecision.PASS, risk_level="low")
