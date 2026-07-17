"""
订单模型
"""
from sqlalchemy import String, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.models.base import Base, UUIDPrimaryKey, TimestampMixin


class Order(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "orders"

    order_no: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    contact_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), nullable=False, index=True
    )
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)

    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )  # pending | paid | shipped | delivered | cancelled | refunding
    payment_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="unpaid"
    )  # unpaid | paid | refunded

    shipping_address: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    logistics_no: Mapped[str | None] = mapped_column(String(200), nullable=True)
    logistics_status: Mapped[str | None] = mapped_column(String(500), nullable=True)

    risk_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    shipped_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
