"""
知识库向量模型 — pgvector 存储
"""
from sqlalchemy import String, Text, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID
from pgvector.sqlalchemy import Vector
from app.models.base import Base, UUIDPrimaryKey, TimestampMixin


class KnowledgeChunk(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "knowledge_chunks"

    product_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True, index=True
    )
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # faq | product_desc | policy | size_chart
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )  # SHA-256
    chunk_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768), nullable=True
    )
    chunk_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
