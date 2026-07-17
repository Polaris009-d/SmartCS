"""
退款记录模型
"""
from sqlalchemy import String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, UUIDPrimaryKey


class RefundRecord(Base, UUIDPrimaryKey):
    """退款交易记录"""
    __tablename__ = "refund_records"

    order_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")  # pending/approved/rejected/processed
    processed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 'ai' or user_id
    approval_rule: Mapped[str | None] = mapped_column(String(200), nullable=True)
    external_refund_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
