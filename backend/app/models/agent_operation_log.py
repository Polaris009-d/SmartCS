"""
Agent 操作审计日志模型
"""
from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.models.base import Base


class AgentOperationLog(Base):
    """Agent 操作的完整审计轨迹，保留 90 天"""
    __tablename__ = "agent_operation_logs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    conversation_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True, index=True
    )
    agent_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # order_agent | logistics_agent | refund_agent
    action: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # order.query | logistics.track | refund.execute
    input_params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    validation_result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    execution_result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # success | rejected | error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
