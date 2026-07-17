"""
FastAPI 应用入口 — SmartCS 企业级智能客服平台
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine
from app.core.redis import get_redis, close_redis
from app.api.router import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化连接，关闭时释放资源"""
    # startup
    await get_redis()
    yield
    # shutdown
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise Intelligent E-commerce Customer Service & Automation Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 API 路由
app.include_router(api_router)


@app.get("/health", tags=["System"])
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "app": settings.APP_NAME, "version": "1.0.0"}
