"""
Embedding 服务 — 调用本地 embedding HTTP 微服务
"""
import json
import httpx
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from app.core.config import settings


class EmbeddingService:
    def __init__(self):
        self.server_url = settings.EMBEDDING_SERVER_URL
        self.dim = settings.EMBEDDING_DIMENSIONS

    async def embed_single(self, text: str) -> list[float]:
        embeddings = await self.embed_batch([text])
        return embeddings[0] if embeddings else [0.0] * self.dim

    async def embed_batch(self, texts: list[str], batch_size: int = 20) -> list[list[float]]:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.server_url}/",
                    content=json.dumps(texts, ensure_ascii=False),
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            print(f"[Embedding] server unavailable: {e}")

        return _tfidf_embed(texts, self.dim)


def _tfidf_embed(texts: list[str], dim: int) -> list[list[float]]:
    tfidf = TfidfVectorizer(max_features=dim, tokenizer=lambda x: jieba.lcut(x), token_pattern=None)
    try:
        tfidf.fit(texts)
    except ValueError:
        tfidf = TfidfVectorizer(max_features=dim, analyzer='char_wb', ngram_range=(2, 4))
        tfidf.fit(texts)
    matrix = tfidf.transform(texts).toarray()
    return [list(row) + [0.0] * (dim - len(row)) for row in matrix]
"""
Embedding 服务 — 调用本地 embedding HTTP 微服务
"""
import json
import httpx
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer

EMBED_SERVER = "http://127.0.0.1:8001"
_dim = 768  # text2vec-base-chinese


class EmbeddingService:
    def __init__(self):
        pass

    async def embed_single(self, text: str) -> list[float]:
        embeddings = await self.embed_batch([text])
        return embeddings[0] if embeddings else [0.0] * _dim

    async def embed_batch(self, texts: list[str], batch_size: int = 20) -> list[list[float]]:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{EMBED_SERVER}/",
                    content=json.dumps(texts, ensure_ascii=False),
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            print(f"[Embedding] server unavailable: {e}")

        return _tfidf_embed(texts, _dim)


def _tfidf_embed(texts: list[str], dim: int) -> list[list[float]]:
    tfidf = TfidfVectorizer(max_features=dim, tokenizer=lambda x: jieba.lcut(x), token_pattern=None)
    try:
        tfidf.fit(texts)
    except ValueError:
        tfidf = TfidfVectorizer(max_features=dim, analyzer='char_wb', ngram_range=(2, 4))
        tfidf.fit(texts)
    matrix = tfidf.transform(texts).toarray()
    return [list(row) + [0.0] * (dim - len(row)) for row in matrix]
