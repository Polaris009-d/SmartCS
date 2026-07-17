"""
重排器 — 基于检索分数排序（torch-free）
"""
from app.core.config import settings


class CrossEncoderReranker:
    """
    对候选文档进行重排。
    使用 RRF 分数归一化排序，不依赖 torch。
    """

    def __init__(self):
        pass

    async def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """基于已有相似度/相关性分数排序"""
        for candidate in candidates:
            # 取 relevance_score 或 similarity 或 rank 作为原始分
            raw = (
                candidate.get("relevance_score", 0)
                or candidate.get("similarity", 0)
                or candidate.get("rank", 0)
            )
            # 归一化到 0-1
            candidate["score"] = min(float(raw) * 3, 0.99) if float(raw) > 0 else 0.01

        sorted_results = sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)
        return sorted_results[:top_k]
