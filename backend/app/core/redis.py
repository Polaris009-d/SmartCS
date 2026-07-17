"""
Redis 连接管理
"""
import redis.asyncio as aioredis
from app.core.config import settings

redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """获取 Redis 连接（惰性初始化连接池）"""
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_pool


async def close_redis():
    """关闭 Redis 连接池"""
    global redis_pool
    if redis_pool is not None:
        await redis_pool.close()
        redis_pool = None
