"""
会话 API — 参考 Chatwoot Conversations API
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.deps import (
    get_current_user, get_conversation_service,
    get_contact_service, get_message_service,
)
from app.models.user import User
from app.models.message import Message
from app.schemas.conversation import (
    ConversationCreate, ConversationUpdate,
    ConversationResponse, ConversationDetailResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.conversation_service import ConversationService
from app.services.contact_service import ContactService
from app.services.message_service import MessageService
from app.services.sse_manager import sse_manager

router = APIRouter()


@router.get("/conversations", response_model=PaginatedResponse[ConversationResponse])
async def list_conversations(
    inbox_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    assigned_agent_id: str | None = Query(default=None),
    contact_id: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    svc: ConversationService = Depends(get_conversation_service),
    _: User = Depends(get_current_user),
):
    conversations, total = await svc.list_conversations(
        inbox_id=inbox_id, status=status,
        assigned_agent_id=assigned_agent_id,
        contact_id=contact_id, priority=priority,
        page=page, page_size=page_size,
    )
    items = [_conversation_to_response(c) for c in conversations]
    return PaginatedResponse.from_items(items=items, total=total, page=page, page_size=page_size)


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    svc: ConversationService = Depends(get_conversation_service),
    contact_svc: ContactService = Depends(get_contact_service),
    msg_svc: MessageService = Depends(get_message_service),
    _: User = Depends(get_current_user),
):
    # 查找或创建联系人
    contact, contact_inbox = await contact_svc.find_or_create_contact(
        email=None, phone=None, name=None,
        inbox_id=data.inbox_id, source_id=data.source_id,
    )

    # 创建会话
    conversation = await svc.create_conversation(
        inbox_id=data.inbox_id,
        contact_id=contact.id,
        contact_inbox_id=contact_inbox.id,
        title=data.title,
        priority=data.priority,
    )

    # 创建系统活动消息
    await msg_svc.create_activity_message(
        conversation_id=conversation.id,
        content="会话已创建",
    )

    # 自动发送 AI 欢迎语
    from datetime import datetime, timezone
    from app.models.message import Message
    welcome = Message(
        conversation_id=conversation.id,
        message_type="outgoing",
        content_type="text",
        content="您好！欢迎来到SmartCS电商平台，我是您的智能客服助手。请问有什么可以帮您的？",
        sender_type="ai",
        private=False,
        created_at=datetime.now(timezone.utc),
    )
    svc.db.add(welcome)
    await svc.db.flush()
    await svc.db.refresh(conversation)

    return _conversation_to_response(conversation)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    svc: ConversationService = Depends(get_conversation_service),
    _: User = Depends(get_current_user),
):
    conversation = await svc.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    messages, _ = await svc.get_messages(conversation_id, page=1, page_size=50)
    resp = _conversation_to_response(conversation)
    from app.schemas.message import MessageResponse
    resp_dict = resp.model_dump()
    resp_dict["messages"] = [MessageResponse.model_validate(m) for m in messages]
    return ConversationDetailResponse(**resp_dict)


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    svc: ConversationService = Depends(get_conversation_service),
    msg_svc: MessageService = Depends(get_message_service),
    current_user: User = Depends(get_current_user),
):
    old = await svc.get_conversation(conversation_id)
    if not old:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    conversation = await svc.update_conversation(conversation_id, data)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # 状态变更发送 activity 消息
    if data.status and data.status != old.status:
        await msg_svc.create_activity_message(
            conversation_id=conversation_id,
            content=f"会话状态变更为 {data.status}",
            content_attributes={"old_status": old.status, "new_status": data.status},
        )

    # 分配变更 SSE 通知
    if data.assigned_agent_id:
        await sse_manager.publish(conversation_id, "assignee.changed", {
            "conversation_id": conversation_id,
            "assigned_agent_id": data.assigned_agent_id,
        })

    # 会话更新 SSE
    await sse_manager.publish(conversation_id, "conversation.updated", {
        "id": conversation_id,
        "status": conversation.status,
        "assigned_agent_id": conversation.assigned_agent_id,
    })

    return _conversation_to_response(conversation)


@router.post("/conversations/{conversation_id}/assign", response_model=ConversationResponse)
async def assign_conversation(
    conversation_id: str,
    agent_id: str = Query(...),
    svc: ConversationService = Depends(get_conversation_service),
    msg_svc: MessageService = Depends(get_message_service),
    current_user: User = Depends(get_current_user),
):
    conversation = await svc.assign_agent(conversation_id, agent_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    await msg_svc.create_activity_message(
        conversation_id=conversation_id,
        content=f"已分配给 {agent_id}",
        content_attributes={"assigned_agent_id": agent_id},
    )

    await sse_manager.publish(conversation_id, "assignee.changed", {
        "conversation_id": conversation_id,
        "assigned_agent_id": agent_id,
    })

    return _conversation_to_response(conversation)


@router.post("/conversations/{conversation_id}/resolve", response_model=ConversationResponse)
async def resolve_conversation(
    conversation_id: str,
    svc: ConversationService = Depends(get_conversation_service),
    msg_svc: MessageService = Depends(get_message_service),
    _: User = Depends(get_current_user),
):
    conversation = await svc.resolve_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    await msg_svc.create_activity_message(
        conversation_id=conversation_id,
        content="会话已解决",
    )

    await sse_manager.publish(conversation_id, "conversation.updated", {
        "id": conversation_id,
        "status": "resolved",
    })

    return _conversation_to_response(conversation)


@router.post("/conversations/{conversation_id}/snooze", response_model=ConversationResponse)
async def snooze_conversation(
    conversation_id: str,
    until: str | None = Query(default=None, description="ISO格式暂缓到期时间"),
    svc: ConversationService = Depends(get_conversation_service),
    msg_svc: MessageService = Depends(get_message_service),
    _: User = Depends(get_current_user),
):
    until_dt = datetime.fromisoformat(until) if until else None
    conversation = await svc.snooze_conversation(conversation_id, until=until_dt)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    await msg_svc.create_activity_message(
        conversation_id=conversation_id,
        content=f"会话已暂缓{'至 ' + until if until else ''}",
    )
    return _conversation_to_response(conversation)


def _conversation_to_response(c) -> ConversationResponse:
    """将 ORM 对象转换为 Pydantic Response（含关联查询占位）"""
    return ConversationResponse(
        id=c.id,
        display_id=c.display_id,
        inbox_id=c.inbox_id,
        contact_id=c.contact_id,
        assigned_agent_id=c.assigned_agent_id,
        status=c.status,
        priority=c.priority,
        title=c.title,
        is_ai_handling=c.is_ai_handling,
        ai_confidence=c.ai_confidence,
        waiting_since=c.waiting_since.isoformat() if c.waiting_since else None,
        first_reply_created_at=c.first_reply_created_at.isoformat() if c.first_reply_created_at else None,
        snoozed_until=c.snoozed_until.isoformat() if c.snoozed_until else None,
        last_activity_at=c.last_activity_at.isoformat() if c.last_activity_at else None,
        resolved_at=c.resolved_at.isoformat() if c.resolved_at else None,
        custom_attributes=c.custom_attributes,
        created_at=c.created_at.isoformat() if c.created_at else "",
        updated_at=c.updated_at.isoformat() if c.updated_at else "",
        unread_count=0,
    )
