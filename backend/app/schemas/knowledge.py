"""
知识库 Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgeSearchRequest(BaseModel):
    q: str = Field(..., min_length=1, description="搜索查询")
    top_k: int = Field(default=5, ge=1, le=20)
    category: str | None = Field(default=None, description="按 source_type 过滤")


class KnowledgeSearchResult(BaseModel):
    id: str
    title: str
    content: str
    source_type: str
    score: float
    product_id: str | None = None


class DocumentUploadResponse(BaseModel):
    id: str
    title: str
    source_type: str
    chunk_count: int
    status: str = "completed"


class DocumentResponse(BaseModel):
    id: str
    title: str
    source_type: str
    content: str
    product_id: str | None = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
