"""
消息 API — 发送消息 + RAG/Agent AI 流式回复
"""
import json
import asyncio
import uuid
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import (
    get_current_user, get_conversation_service,
    get_contact_service, get_message_service,
)
from app.models.user import User
from app.models.inbox import Inbox
from app.schemas.message import MessageCreate, MessageResponse
from app.schemas.common import PaginatedResponse
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from app.services.sse_manager import sse_manager

# AI 组件
from app.llm.factory import get_llm_provider
from app.rag.embedding import EmbeddingService
from app.rag.hybrid_retriever import HybridRetriever
from app.rag.reranker import CrossEncoderReranker
from app.rag.generator import RAGGenerator
from app.agents.router import AgentRouter, extract_order_no
from app.agents.safety_engine import SafetyEngine
from app.agents.tools.order_tools import OrderTool
from app.agents.tools.logistics_tools import LogisticsTool
from app.agents.order_agent import OrderAgent
from app.agents.logistics_agent import LogisticsAgent
from app.agents.refund_agent import RefundAgent
from app.agents.tools.refund_tools import RefundTool
from app.models.agent_operation_log import AgentOperationLog

router = APIRouter()


def _create_agent_router(db: AsyncSession) -> AgentRouter:
    """创建并配置 Agent 路由器"""
    safety = SafetyEngine()
    agent_router = AgentRouter()
    agent_router.register(OrderAgent(safety, OrderTool(db)))
    agent_router.register(LogisticsAgent(safety, LogisticsTool(db), OrderTool(db)))
    agent_router.register(RefundAgent(safety, RefundTool(db), OrderTool(db)))
    return agent_router


@router.get("/conversations/{conversation_id}/messages", response_model=PaginatedResponse[MessageResponse])
async def list_messages(
    conversation_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    svc: ConversationService = Depends(get_conversation_service),
    _: User = Depends(get_current_user),
):
    """获取会话消息历史"""
    conversation = await svc.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")

    messages, total = await svc.get_messages(conversation_id, page=page, page_size=page_size)
    items = [MessageResponse.model_validate(m) for m in messages]
    return PaginatedResponse.from_items(items=items, total=total, page=page, page_size=page_size)


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    svc: ConversationService = Depends(get_conversation_service),
    msg_svc: MessageService = Depends(get_message_service),
    current_user: User = Depends(get_current_user),
):
    """
    发送消息到会话。客户消息自动触发 AI 处理流程。
    返回 SSE 流式响应。
    """
    conversation = await svc.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")

    if data.message_type == "incoming":
        # 1. 创建客户入站消息
        msg = await msg_svc.create_incoming_message(
            conversation_id=conversation_id,
            content=data.content,
            sender_type="contact",
            sender_id=conversation.contact_id,
            content_type=data.content_type,
            source_id=data.source_id or str(uuid.uuid4()),
            content_attributes=data.content_attributes,
        )

        # 0. 首次消息 → pending → open
        if conversation.status == "pending":
            conversation.status = "open"
            conversation.is_ai_handling = True
            await db.flush()
            await sse_manager.publish(conversation_id, "conversation.updated", {
                "id": conversation_id, "status": "open",
            })

        # 1.5. 情感分析
        sent_alert = None
        try:
            from app.services.sentiment_service import SentimentService
            sent_svc = SentimentService(db)
            sent_alert = await sent_svc.check_and_alert(
                conversation_id=conversation_id,
                message_id=msg.id,
                customer_id=conversation.contact_id,
                message=data.content,
            )
            if sent_alert:
                await sse_manager.publish(conversation_id, "sentiment_alert", {
                    "alert_id": sent_alert.id,
                    "score": sent_alert.sentiment_score,
                    "label": sent_alert.sentiment_label,
                    "alert_level": sent_alert.alert_level,
                    "is_escalated": sent_alert.is_escalated,
                })
        except Exception:
            pass

        # 2. SSE 流式 AI 处理（RAG + Agent）
        conv_context = (conversation.custom_attributes or {}).get("context", {})
        return StreamingResponse(
            _ai_reply_stream(
                conversation_id=conversation_id,
                user_message=data.content,
                contact_id=conversation.contact_id,
                conv_context=conv_context,
                sent_alert=sent_alert,
                db=db,
                msg_svc=msg_svc,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # 客服手动回复 → AI 不再处理
        if conversation.is_ai_handling:
            conversation.is_ai_handling = False
            await db.flush()
        msg = await msg_svc.create_outgoing_message(
            conversation_id=conversation_id,
            content=data.content,
            sender_type="user",
            sender_id=current_user.id,
            content_type=data.content_type,
            private=data.private,
            content_attributes=data.content_attributes,
        )
        return MessageResponse.model_validate(msg)


async def _ai_reply_stream(
    conversation_id: str,
    user_message: str,
    contact_id: str,
    conv_context: dict,
    sent_alert=None,
    db: AsyncSession = None,
    msg_svc: MessageService = None,
):
    # 情感严重告警 → 直接生成 LLM 安抚话术
    if sent_alert and hasattr(sent_alert, 'alert_level') and sent_alert.alert_level == "critical":
        comfort = await _generate_comfort_message(user_message)
        for i, char in enumerate(comfort):
            yield f"event: ai_chunk\ndata: {json.dumps({'chunk': char, 'index': i})}\n\n"
            await asyncio.sleep(0.02)
        await msg_svc.create_ai_message(conversation_id=conversation_id, content=comfort, content_attributes={"type": "comfort"})
        yield f"event: ai_done\ndata: {json.dumps({'full_content': comfort, 'confidence': 1.0, 'sources': [], 'type': 'comfort'})}\n\n"
        return
    """
    核心 AI 处理流程：
    1. 尝试 AgentRouter (Order / Logistics)
    2. Agent 不匹配 → RAG Pipeline
    3. 流式输出结果到 SSE
    """
    # 发送 thinking 事件
    yield f"event: thinking\ndata: {json.dumps({'message': 'AI 正在思考...'})}\n\n"

    # === 阶段 1: Agent 路由 ===
    ctx = dict(conv_context)
    ctx["contact_id"] = contact_id

    agent_router = _create_agent_router(db)
    agent_result = await agent_router.execute(
        user_message=user_message,
        conversation_id=conversation_id,
        context=ctx,
    )

    # Agent 执行后，保存上下文（如查到的订单号）—— 合并到现有 custom_attributes
    if agent_result is not None and agent_result.data:
        order_no = (agent_result.data or {}).get("order_no")
        if order_no:
            from sqlalchemy import update, select
            from app.models.conversation import Conversation
            # 读取现有 custom_attributes 并合并
            existing_q = await db.execute(
                select(Conversation.custom_attributes).where(Conversation.id == conversation_id)
            )
            existing_attrs = existing_q.scalar() or {}
            existing_context = existing_attrs.get("context", {})
            existing_context["last_order_no"] = order_no
            existing_attrs["context"] = existing_context
            await db.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(custom_attributes=existing_attrs)
            )
            await db.commit()

    if agent_result is not None:
        # Agent 匹配成功 — 处理结果
        await _handle_agent_result(conversation_id, agent_result, db, msg_svc)

        if agent_result.success:
            reply = _format_agent_success(agent_result)
        else:
            reply = agent_result.message
            # 失败的退款加安抚话术
            if "refund" in agent_result.action:
                reply += "\n\n非常抱歉给您带来不便，您的退款申请已转交人工客服优先处理，请稍候。"

        # 流式输出回复
        for i, char in enumerate(reply):
            yield f"event: ai_chunk\ndata: {json.dumps({'chunk': char, 'index': i})}\n\n"
            await asyncio.sleep(0.02)

        # 构建 agent_action 数据并发送到 SSE 流
        agent_event_data = {
            "action": agent_result.action,
            "status": "success" if agent_result.success else "failed",
            "message": agent_result.message,
            "details": agent_result.data,
        }
        if agent_result.action in ("refund.list", "order.list", "logistics.list") and agent_result.data:
            agent_event_data["orders"] = agent_result.data.get("orders", [])
            agent_event_data["last_order_no"] = agent_result.data.get("last_order_no")
        # 同时发送到 SSE 推送通道 和 HTTP 响应流
        yield f"event: agent_action\ndata: {json.dumps(agent_event_data, ensure_ascii=False)}\n\n"
        await sse_manager.publish(conversation_id, "agent_action", agent_event_data)

        done_data = json.dumps({"message_id": "", "full_content": reply, "confidence": 1.0, "sources": []})
        yield f"event: ai_done\ndata: {done_data}\n\n"
        return

    # === 阶段 2: RAG Pipeline ===
    try:
        embedding_svc = EmbeddingService()
        retriever = HybridRetriever(db, embedding_svc)
        reranker = CrossEncoderReranker()
        generator = RAGGenerator()

        # 检索 + 重排
        candidates = await retriever.search(user_message, top_k=10)
        if candidates:
            top_chunks = await reranker.rerank(user_message, candidates, top_k=5)
        else:
            top_chunks = []

        if not top_chunks:
            # 完全没有检索结果 → 转人工
            from sqlalchemy import update
            from app.models.conversation import Conversation
            await db.execute(update(Conversation).where(Conversation.id == conversation_id).values(is_ai_handling=False))
            await db.commit()
            handoff_msg = json.dumps({"reason": "no_results", "confidence": 0.0})
            yield f"event: handoff\ndata: {handoff_msg}\n\n"
            reply = "抱歉，我暂时无法准确回答您的问题，正在为您转接人工客服，请稍候。"
            for i, char in enumerate(reply):
                yield f"event: ai_chunk\ndata: {json.dumps({'chunk': char, 'index': i})}\n\n"
                await asyncio.sleep(0.02)
            yield f"event: ai_done\ndata: {json.dumps({'message_id': '', 'full_content': reply, 'confidence': 0.0, 'sources': [], 'handoff': True})}\n\n"
            return

        # 有检索结果 → 直接用 LLM 生成
        max_score = top_chunks[0].get("score", 0)
        decision = "auto_reply"

        # 取最近 5 条消息作为对话历史
        from sqlalchemy import select as sql_select, desc as sql_desc
        from app.models.message import Message
        q = sql_select(Message).where(
            Message.conversation_id == conversation_id,
            Message.message_type != "activity",
        ).order_by(sql_desc(Message.created_at)).limit(5)
        result = await db.execute(q)
        recent_msgs = list(result.scalars().all())[::-1]  # 反转回时间顺序
        chat_history = [
            {"role": "user" if m.sender_type == "contact" else "assistant", "content": m.content}
            for m in recent_msgs
        ]

        context = generator._build_context(top_chunks)
        messages = generator._build_messages(user_message, context, chat_history)

        full_content = ""
        async for token in generator.llm.chat_stream(messages, temperature=0.3, max_tokens=512):
            full_content += token
            yield f"event: ai_chunk\ndata: {json.dumps({'chunk': token, 'index': len(full_content)})}\n\n"
            await asyncio.sleep(0.01)

        # 保存 AI 消息
        sources_data = [
            {"title": c.get("title", ""), "content": c.get("content", "")[:200], "score": c.get("score", 0)}
            for c in top_chunks[:3]
        ]
        await msg_svc.create_ai_message(
            conversation_id=conversation_id,
            content=full_content,
            ai_confidence=max_score,
            content_attributes={"sources": sources_data, "decision": decision},
        )

        done_data = json.dumps({
            "message_id": "",
            "full_content": full_content,
            "confidence": max_score,
            "sources": sources_data,
            "decision": decision,
        })
        yield f"event: ai_done\ndata: {done_data}\n\n"

    except Exception as e:
        # RAG 失败降级：mock 回复
        fallback = _mock_fallback_reply(user_message)
        for i, char in enumerate(fallback):
            yield f"event: ai_chunk\ndata: {json.dumps({'chunk': char, 'index': i})}\n\n"
            await asyncio.sleep(0.02)
        yield f"event: ai_done\ndata: {json.dumps({'message_id': '', 'full_content': fallback, 'confidence': 0.0, 'sources': []})}\n\n"


async def _handle_agent_result(
    conversation_id: str,
    result,
    db: AsyncSession,
    msg_svc: MessageService,
):
    """记录 Agent 执行结果到审计日志 + 消息表"""
    import time as _time
    log = AgentOperationLog(
        conversation_id=conversation_id,
        agent_type=_agent_type_from_action(result.action),
        action=result.action,
        input_params=getattr(result, '_input_params', {}) or {},
        validation_result={
            "allowed": result.safety_result.allowed if result.safety_result else False,
            "decision": result.safety_result.decision.value if result.safety_result else "unknown",
        },
        execution_result=result.data or {},
        status="success" if result.success else "rejected",
        error_message=None if result.success else result.message,
        execution_time_ms=result.execution_time_ms,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.flush()


def _agent_type_from_action(action: str) -> str:
    if action.startswith("order."):
        return "order_agent"
    elif action.startswith("logistics."):
        return "logistics_agent"
    elif action.startswith("refund."):
        return "refund_agent"
    return "unknown"


def _format_agent_success(result) -> str:
    """格式化 Agent 成功结果为自然语言"""
    data = result.data or {}
    if result.action == "order.query":
        return (
            f"已为您查到订单 {data.get('order_no', '')}：\n"
            f"商品：{data.get('product_name', '')}\n"
            f"数量：{data.get('quantity', 0)} 件\n"
            f"金额：¥{data.get('total_amount', 0)}\n"
            f"状态：{_translate_status(data.get('status', ''))}\n"
            f"物流单号：{data.get('logistics_no', '暂无')}\n"
            f"物流状态：{data.get('logistics_status', '暂无')}"
        )
    elif result.action == "logistics.track":
        if data.get("logistics_no"):
            return (
                f"订单 {data.get('order_no', '')} 的物流信息：\n"
                f"快递单号：{data.get('logistics_no', '')}\n"
                f"当前状态：{data.get('logistics_status', '')}\n"
                f"详细轨迹：\n{data.get('tracking_details', '')}"
            )
        return data.get("message", "暂无物流信息")
    elif result.action == "refund.execute":
        return (
            f"退款申请已提交成功！\n"
            f"退款编号：{data.get('external_refund_id', '')}\n"
            f"退款金额：¥{data.get('amount', 0)}\n"
            f"预计到账时间：{data.get('estimated_arrival', '1-3个工作日')}\n"
            f"款项将原路退回到您的支付账户，请留意查收。"
        )
    elif result.action == "refund.list":
        orders = data.get("orders", [])
        return f"请选择要退款的订单（共{len(orders)}个）："
    elif result.action == "order.list":
        orders = data.get("orders", [])
        return f"请选择要查询的订单（共{len(orders)}个）："
    elif result.action == "logistics.list":
        orders = data.get("orders", [])
        return f"请选择要查物流的订单（共{len(orders)}个已发货）："
    return "操作完成"


def _translate_status(status: str) -> str:
    mapping = {
        "pending": "待付款", "paid": "已付款", "shipped": "已发货",
        "delivered": "已签收", "cancelled": "已取消", "refunding": "退款中",
    }
    return mapping.get(status, status)


COMFORT_PROMPT = """你是电商客服，客户刚才发了一条非常不满的消息。请生成一条安抚话术，要求：
1. 真诚道歉，不要推卸责任
2. 表达重视并承诺优先处理
3. 控制在80字以内
4. 只返回话术本身，不要其他内容

客户消息：{message}"""


async def _generate_comfort_message(user_message: str) -> str:
    """调用 LLM 生成安抚话术"""
    try:
        from app.llm.factory import get_llm_provider
        from app.llm.base import ChatMessage
        llm = get_llm_provider()
        prompt = COMFORT_PROMPT.format(message=user_message[:300])
        resp = await llm.chat([ChatMessage(role="user", content=prompt)], temperature=0.5, max_tokens=150)
        return resp.content.strip()
    except Exception:
        return "非常抱歉给您带来不愉快的体验，我们已收到您的反馈，客服专员将优先为您处理，请稍候。"


def _mock_fallback_reply(user_message: str) -> str:
    """当 RAG/LLM 不可用时的降级 mock 回复"""
    if "尺码" in user_message or "码" in user_message:
        return "根据您提供的信息，我建议您选择 L 码。如果您偏好修身版型可以选 M 码，喜欢宽松可以选 XL 码。"
    elif "你好" in user_message or "您好" in user_message:
        return "您好！我是智能客服助手，很高兴为您服务。有什么可以帮您的？"
    else:
        return "感谢您的咨询！关于您的问题，我需要更多信息来帮您准确回复。您可以提供订单号或告诉我具体的商品名称。"
