"""
SSE 订阅端点 — 参考 Chatwoot ActionCable 的频道模型。
客户端通过此端点订阅会话的实时事件流。
"""
import json
import asyncio
import time
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from app.api.deps import get_current_user, get_conversation_service
from app.models.user import User
from app.services.conversation_service import ConversationService
from app.services.sse_manager import sse_manager

router = APIRouter()


@router.get("/conversations/{conversation_id}/stream")
async def stream_conversation(
    conversation_id: str,
    token: str = Query(..., description="JWT令牌"),
    svc: ConversationService = Depends(get_conversation_service),
):
    """
    订阅会话的 SSE 事件流。
    客户端使用 EventSource 连接此端点接收实时消息推送。

    事件类型:
      - message.created: 新消息
      - ai_chunk: AI 流式回复逐字片段
      - ai_done: AI 回复完成
      - agent_action: Agent 工具执行结果
      - conversation.updated: 会话状态/分配变更
      - assignee.changed: 分配变更
      - handoff: AI 转人工
      - typing: 客服正在输入
      - keepalive: 心跳（30s）
    """
    # 通过 token 验证用户
    from app.core.security import decode_access_token
    from sqlalchemy import select
    from app.core.database import async_session_factory
    from app.models.user import User as UserModel

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    async with async_session_factory() as db:
        result = await db.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        # 验证会话存在
        conversation = await svc.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    queue = await sse_manager.subscribe(conversation_id)

    async def event_generator():
        try:
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield payload
                except asyncio.TimeoutError:
                    # 心跳
                    yield f"event: keepalive\ndata: {json.dumps({'ts': time.time()})}\n\n"
                except asyncio.CancelledError:
                    break
        finally:
            await sse_manager.unsubscribe(conversation_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/agents/{agent_id}/stream")
async def stream_agent(
    agent_id: str,
    token: str = Query(..., description="JWT令牌"),
):
    """
    订阅客服全局通知流。
    接收新会话分配、系统告警等全局事件。
    """
    try:
        payload = __import__("app.core.security", fromlist=["decode_access_token"]).decode_access_token(token)
        user_id = payload.get("sub")
        if user_id != agent_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token与Agent不匹配")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    queue = await sse_manager.subscribe_agent(agent_id)

    async def event_generator():
        try:
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield payload
                except asyncio.TimeoutError:
                    yield f"event: keepalive\ndata: {json.dumps({'ts': time.time()})}\n\n"
                except asyncio.CancelledError:
                    break
        finally:
            await sse_manager.unsubscribe_agent(agent_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
