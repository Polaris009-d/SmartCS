"""
Agent 基类
"""
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from app.agents.safety_engine import SafetyEngine, SafetyResult


@dataclass
class AgentResult:
    success: bool
    action: str
    data: dict | None = None
    message: str = ""
    safety_result: SafetyResult | None = None
    execution_time_ms: int = 0


class BaseAgent(ABC):
    """Agent 基类 — 所有 Agent 需实现此接口"""

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Agent 类型标识：order_agent | logistics_agent | refund_agent"""
        ...

    @abstractmethod
    def match(self, user_message: str) -> bool:
        """判断此 Agent 是否能处理用户的意图（关键词匹配/意图分类）"""
        ...

    @abstractmethod
    async def execute(self, conversation_id: str, user_message: str, context: dict | None = None) -> AgentResult:
        """执行 Agent 操作，包含安全校验 + 业务执行 + 审计日志"""
        ...

    def __init__(self, safety_engine: SafetyEngine):
        self.safety_engine = safety_engine

    async def _run_with_safety(
        self,
        action: str,
        params: dict,
        conversation_id: str,
        business_context: dict,
        execute_fn,
    ) -> AgentResult:
        """
        带安全校验的通用执行流程。
        5 层安全模型的核心实现。
        """
        start = time.time()

        # Layer 2-3: 安全校验
        safety = self.safety_engine.validate(action, params, business_context)

        if not safety.allowed:
            elapsed_ms = int((time.time() - start) * 1000)
            return AgentResult(
                success=False,
                action=action,
                message=safety.reason or "操作被拒绝",
                safety_result=safety,
                execution_time_ms=elapsed_ms,
            )

        # Layer 4: 执行
        try:
            result_data = await execute_fn(params, business_context)
            elapsed_ms = int((time.time() - start) * 1000)
            return AgentResult(
                success=True,
                action=action,
                data=result_data,
                message="操作成功",
                safety_result=safety,
                execution_time_ms=elapsed_ms,
            )
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            return AgentResult(
                success=False,
                action=action,
                message=f"执行失败: {str(e)}",
                safety_result=safety,
                execution_time_ms=elapsed_ms,
            )
