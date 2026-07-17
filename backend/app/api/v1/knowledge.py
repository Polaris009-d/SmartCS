"""
知识库 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.knowledge import KnowledgeSearchRequest, KnowledgeSearchResult, DocumentResponse
from app.rag.embedding import EmbeddingService
from app.rag.chunker import DocumentChunker
from app.rag.hybrid_retriever import HybridRetriever
from app.rag.reranker import CrossEncoderReranker
from app.models.knowledge_chunk import KnowledgeChunk
import hashlib

router = APIRouter()


@router.get("/knowledge/search", response_model=list[KnowledgeSearchResult])
async def search_knowledge(
    q: str = Query(..., min_length=1),
    top_k: int = Query(default=5, ge=1, le=20),
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """混合检索知识库"""
    embedding_svc = EmbeddingService()
    retriever = HybridRetriever(db, embedding_svc)
    reranker = CrossEncoderReranker()

    candidates = await retriever.search(q, top_k=top_k * 3, source_type=category)
    if not candidates:
        return []

    # 重排
    ranked = await reranker.rerank(q, candidates, top_k=top_k)

    return [
        KnowledgeSearchResult(
            id=r["id"],
            title=r.get("title", ""),
            content=r.get("content", ""),
            source_type=r.get("source_type", ""),
            score=r.get("score", 0.0),
            product_id=r.get("product_id"),
        )
        for r in ranked
    ]


@router.post("/knowledge/documents", response_model=dict)
async def upload_document(
    file: UploadFile = File(...),
    source_type: str = Form(default="faq"),
    product_id: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """上传文档到知识库（分块→向量化→入库）"""
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件读取失败: {e}")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("gbk", errors="ignore")

    # 分块
    chunker = DocumentChunker()
    chunks = chunker.chunk(
        text,
        source_type=source_type,
        title=file.filename or "unnamed",
        product_id=product_id,
    )

    # 给每个 chunk 加标题
    filename = file.filename or "unnamed"
    for c in chunks:
        meta = c.get("chunk_metadata", {})
        meta["source_file"] = filename
        # 取内容第一行或前30字作为标题
        first_line = c["content"].split("\n")[0].strip()
        title = first_line if 2 <= len(first_line) <= 50 else c["content"][:30].strip()
        c["chunk_metadata"] = meta
        c["title"] = title

    # 向量化
    embedding_svc = EmbeddingService()
    chunk_texts = [c["content"] for c in chunks]
    embeddings = await embedding_svc.embed_batch(chunk_texts)

    # 入库
    inserted = 0
    for i, chunk in enumerate(chunks):
        content_hash = hashlib.sha256(chunk["content"].encode()).hexdigest()
        # 检查去重
        from sqlalchemy import select
        existing = await db.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.content_hash == content_hash)
        )
        if existing.scalar_one_or_none():
            continue

        kc = KnowledgeChunk(
            product_id=product_id,
            source_type=source_type,
            title=chunk.get("title", chunk.get("chunk_metadata", {}).get("title", "")),
            content=chunk["content"],
            content_hash=content_hash,
            chunk_index=i,
            embedding=embeddings[i] if i < len(embeddings) else None,
            chunk_metadata=chunk.get("chunk_metadata", chunk.get("metadata", {})),
        )
        db.add(kc)
        inserted += 1

    await db.flush()

    return {
        "filename": file.filename,
        "source_type": source_type,
        "chunk_count": len(chunks),
        "inserted": inserted,
        "duplicates": len(chunks) - inserted,
    }


@router.get("/knowledge/documents", response_model=list[DocumentResponse])
async def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """知识库文档列表"""
    from sqlalchemy import select, func
    from sqlalchemy import desc

    q = select(KnowledgeChunk).where(
        KnowledgeChunk.is_active == True
    ).order_by(desc(KnowledgeChunk.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size)

    result = await db.execute(q)
    chunks = result.scalars().all()
    return [DocumentResponse.model_validate(c) for c in chunks]


@router.delete("/knowledge/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """删除知识库文档（软删除）"""
    from sqlalchemy import select
    result = await db.execute(
        select(KnowledgeChunk).where(KnowledgeChunk.id == doc_id)
    )
    chunk = result.scalar_one_or_none()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    chunk.is_active = False
    await db.flush()
