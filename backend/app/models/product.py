"""
商品模型
"""
from sqlalchemy import String, Integer, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import Base, UUIDPrimaryKey, TimestampMixin


class Product(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    specs: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )  # {"color": ["红","蓝"], "size": ["S","M","L"]}
    size_chart: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )  # [{"height_cm": 175, "weight_kg": 70, "recommend_size": "L"}]
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # active | inactive | discontinued
    image_urls: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=list
    )
