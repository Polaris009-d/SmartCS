"""
混合检索器 — Dense (pgvector) + Sparse (BM25/tsvector) + RRF 融合
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.rag.embedding import EmbeddingService
from app.core.config import settings


class HybridRetriever:
    """
    混合检索：pgvector 稠密向量 + PostgreSQL tsvector 稀疏检索 + RRF 融合。
    参考 LangChain EnsembleRetriever 思路，但直接基于 pgvector 实现以获得更好性能。
    """

    def __init__(self, db: AsyncSession, embedding_service: EmbeddingService):
        self.db = db
        self.embedding = embedding_service

    async def search(
        self,
        query: str,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> list[dict]:
        """执行混合检索，返回 top-k 结果"""
        # 生成查询向量
        query_embedding = await self.embedding.embed_single(query)

        # 稠密检索 (pgvector ANN)
        dense_results = await self._dense_search(query_embedding, top_k=settings.RAG_DENSE_TOP_K, source_type=source_type)

        # 稀疏检索 (PostgreSQL tsvector)
        sparse_results = await self._sparse_search(query, top_k=settings.RAG_SPARSE_TOP_K, source_type=source_type)

        # RRF 融合
        fused = self._rrf_fusion(dense_results, sparse_results, k=settings.RAG_RRF_K)

        # 取 top-k
        return fused[:top_k]

    async def _dense_search(
        self,
        query_embedding: list[float],
        top_k: int = 20,
        source_type: str | None = None,
    ) -> list[dict]:
        """pgvector 余弦相似度 ANN 搜索"""
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        params: dict = {"embedding": embedding_str, "top_k": top_k}
        if source_type:
            sql = text("""
                SELECT id, title, content, source_type, product_id,
                       1 - (embedding <=> CAST(:embedding AS vector)) AS similarity,
                       chunk_metadata
                FROM knowledge_chunks
                WHERE is_active = true
                  AND embedding IS NOT NULL
                  AND source_type = :source_type
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
            """)
            params["source_type"] = source_type
        else:
            sql = text("""
                SELECT id, title, content, source_type, product_id,
                       1 - (embedding <=> CAST(:embedding AS vector)) AS similarity,
                       chunk_metadata
                FROM knowledge_chunks
                WHERE is_active = true
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
            """)
        result = await self.db.execute(sql, params)
        return [dict(row._mapping) for row in result]

    async def _sparse_search(
        self,
        query: str,
        top_k: int = 20,
        source_type: str | None = None,
    ) -> list[dict]:
        """PostgreSQL tsvector 全文检索"""
        params: dict = {"query": query, "top_k": top_k}
        if source_type:
            sql = text("""
                SELECT id, title, content, source_type, product_id,
                       ts_rank(
                           to_tsvector('simple', content),
                           plainto_tsquery('simple', :query)
                       ) AS rank,
                       chunk_metadata
                FROM knowledge_chunks
                WHERE is_active = true
                  AND source_type = :source_type
                  AND to_tsvector('simple', content) @@ plainto_tsquery('simple', :query)
                ORDER BY rank DESC
                LIMIT :top_k
            """)
            params["source_type"] = source_type
        else:
            sql = text("""
                SELECT id, title, content, source_type, product_id,
                       ts_rank(
                           to_tsvector('simple', content),
                           plainto_tsquery('simple', :query)
                       ) AS rank,
                       chunk_metadata
                FROM knowledge_chunks
                WHERE is_active = true
                  AND to_tsvector('simple', content) @@ plainto_tsquery('simple', :query)
                ORDER BY rank DESC
                LIMIT :top_k
            """)
        result = await self.db.execute(sql, params)
        return [dict(row._mapping) for row in result]

    def _rrf_fusion(
        self,
        dense: list[dict],
        sparse: list[dict],
        k: int = 60,
    ) -> list[dict]:
        """Reciprocal Rank Fusion — 融合稠密和稀疏排名"""
        scores: dict[str, float] = {}
        result_map: dict[str, dict] = {}

        # 稠密排名
        for rank, item in enumerate(dense, start=1):
            item_id = str(item["id"])
            result_map[item_id] = item
            scores[item_id] = scores.get(item_id, 0) + 1.0 / (k + rank)

        # 稀疏排名
        for rank, item in enumerate(sparse, start=1):
            item_id = str(item["id"])
            result_map[item_id] = item
            scores[item_id] = scores.get(item_id, 0) + 1.0 / (k + rank)

        # 按 RRF 分数排序
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        results = []
        for item_id in sorted_ids:
            item = result_map[item_id]
            # 处理 similarity/rank 字段（可能是 decimal 类型，转换为 float）
            similarity = item.get("similarity")
            rank_val = item.get("rank")
            item["relevance_score"] = scores[item_id]
            item["similarity"] = float(similarity) if similarity is not None else None
            item["rank"] = float(rank_val) if rank_val is not None else None
            results.append(item)

        return results
"""
混合检索器 — Dense (pgvector) + Sparse (BM25/tsvector) + RRF 融合
"""
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from app.models.knowledge_chunk import KnowledgeChunk
from app.rag.embedding import EmbeddingService
from app.core.config import settings


class HybridRetriever:
    """
    混合检索：pgvector 稠密向量 + PostgreSQL tsvector 稀疏检索 + RRF 融合。
    参考 LangChain EnsembleRetriever 思路，但直接基于 pgvector 实现以获得更好性能。
    """

    def __init__(self, db: AsyncSession, embedding_service: EmbeddingService):
        self.db = db
        self.embedding = embedding_service

    async def search(
        self,
        query: str,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> list[dict]:
        """执行混合检索，返回 top-k 结果"""
        # 生成查询向量
        query_embedding = await self.embedding.embed_single(query)

        # 稠密检索 (pgvector ANN)
        dense_results = await self._dense_search(query_embedding, top_k=settings.RAG_DENSE_TOP_K, source_type=source_type)

        # 稀疏检索 (PostgreSQL tsvector)
        sparse_results = await self._sparse_search(query, top_k=settings.RAG_SPARSE_TOP_K, source_type=source_type)

        # RRF 融合
        fused = self._rrf_fusion(dense_results, sparse_results, k=settings.RAG_RRF_K)

        # 取 top-k
        return fused[:top_k]

    async def _dense_search(
        self,
        query_embedding: list[float],
        top_k: int = 20,
        source_type: str | None = None,
    ) -> list[dict]:
        """pgvector 余弦相似度 ANN 搜索"""
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        conditions = "is_active = true"
        if source_type:
            conditions += f" AND source_type = '{source_type}'"

        sql = text(f"""
            SELECT id, title, content, source_type, product_id,
                   1 - (embedding <=> '{embedding_str}'::vector) AS similarity,
                   chunk_metadata
            FROM knowledge_chunks
            WHERE {conditions}
              AND embedding IS NOT NULL
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT {top_k}
        """)
        result = await self.db.execute(sql)
        return [dict(row._mapping) for row in result]

    async def _sparse_search(
        self,
        query: str,
        top_k: int = 20,
        source_type: str | None = None,
    ) -> list[dict]:
        """PostgreSQL tsvector 全文检索"""
        conditions = "is_active = true"
        if source_type:
            conditions += f" AND source_type = '{source_type}'"

        sql = text(f"""
            SELECT id, title, content, source_type, product_id,
                   ts_rank(
                       to_tsvector('simple', content),
                       plainto_tsquery('simple', :query)
                   ) AS rank,
                   chunk_metadata
            FROM knowledge_chunks
            WHERE {conditions}
              AND to_tsvector('simple', content) @@ plainto_tsquery('simple', :query)
            ORDER BY rank DESC
            LIMIT {top_k}
        """)
        result = await self.db.execute(sql, {"query": query})
        return [dict(row._mapping) for row in result]

    def _rrf_fusion(
        self,
        dense: list[dict],
        sparse: list[dict],
        k: int = 60,
    ) -> list[dict]:
        """Reciprocal Rank Fusion — 融合稠密和稀疏排名"""
        scores: dict[str, dict] = {}
        result_map: dict[str, dict] = {}

        # 稠密排名
        for rank, item in enumerate(dense, start=1):
            entry = result_map.get(item["id"], item)
            result_map[item["id"]] = entry
            scores[item["id"]] = scores.get(item["id"], 0) + 1.0 / (k + rank)

        # 稀疏排名
        for rank, item in enumerate(sparse, start=1):
            entry = result_map.get(item["id"], item)
            result_map[item["id"]] = entry
            scores[item["id"]] = scores.get(item["id"], 0) + 1.0 / (k + rank)

        # 按 RRF 分数排序
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        results = []
        for item_id in sorted_ids:
            item = result_map[item_id]
            # 处理 similarity/rank 字段（可能是 decimal 类型，转换为 float）
            similarity = item.get("similarity")
            rank_val = item.get("rank")
            item["relevance_score"] = scores[item_id]
            item["similarity"] = float(similarity) if similarity is not None else None
            item["rank"] = float(rank_val) if rank_val is not None else None
            results.append(item)

        return results
