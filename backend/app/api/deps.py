"""
FastAPI 依赖注入 — 提供 DB session、当前用户、Service 实例等
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.services.inbox_service import InboxService
from app.services.contact_service import ContactService
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 JWT 令牌中解析当前用户"""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


async def get_inbox_service(db: AsyncSession = Depends(get_db)) -> InboxService:
    return InboxService(db)


async def get_contact_service(db: AsyncSession = Depends(get_db)) -> ContactService:
    return ContactService(db)


async def get_conversation_service(db: AsyncSession = Depends(get_db)) -> ConversationService:
    return ConversationService(db)


async def get_message_service(db: AsyncSession = Depends(get_db)) -> MessageService:
    return MessageService(db)
