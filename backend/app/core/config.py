"""
应用配置管理 — 基于 pydantic-settings
所有环境变量通过 Settings 类统一管理，支持 .env 文件加载
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === Application ===
    APP_NAME: str = "SmartCS"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8000"

    # === Database ===
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/smartcs"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # === Redis ===
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SESSION_TTL: int = 86400  # 24h
    REDIS_SEMANTIC_CACHE_TTL: int = 3600  # 1h

    # === LLM ===
    LLM_PROVIDER: str = "openai"  # openai | anthropic | local
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 2048
    LLM_TIMEOUT: int = 30

    # === LLM API Keys ===
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # === Embedding ===
    EMBEDDING_PROVIDER: str = "openai"  # openai | local
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 768

    # === Reranker ===
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RERANKER_DEVICE: str = "cpu"

    # === RAG ===
    RAG_DENSE_TOP_K: int = 20
    RAG_SPARSE_TOP_K: int = 20
    RAG_RRF_K: int = 60
    RAG_RERANK_TOP_K: int = 5
    RAG_CONFIDENCE_HIGH: float = 0.75
    RAG_CONFIDENCE_MEDIUM: float = 0.50

    # === Agent Safety ===
    AUTO_REFUND_MAX_AMOUNT: float = 200.0
    AUTO_REFUND_MAX_DAILY: int = 2
    COUPON_DAILY_LIMIT: int = 50
    COUPON_SINGLE_MAX: float = 10.0

    # === Sentiment ===
    SENTIMENT_THRESHOLD: float = 0.7
    SENTIMENT_CRITICAL_THRESHOLD: float = 0.9

    # === Audit ===
    AUDIT_LOG_RETENTION_DAYS: int = 90

    # === Rate Limiting ===
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_MINUTE_AUTH: int = 500

    # === JWT ===
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # === External APIs ===
    LOGISTICS_API_URL: Optional[str] = None
    LOGISTICS_API_KEY: Optional[str] = None
    PAYMENT_API_URL: Optional[str] = None
    PAYMENT_API_KEY: Optional[str] = None

    # === Embedding Server ===
    EMBEDDING_SERVER_URL: str = "http://127.0.0.1:8001"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
