"""
渠道 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user, get_inbox_service
from app.models.user import User
from app.schemas.inbox import InboxCreate, InboxUpdate, InboxResponse
from app.services.inbox_service import InboxService

router = APIRouter()


@router.get("/inboxes", response_model=list[InboxResponse])
async def list_inboxes(
    svc: InboxService = Depends(get_inbox_service),
    _: User = Depends(get_current_user),
):
    inboxes = await svc.list_inboxes()
    return inboxes


@router.post("/inboxes", response_model=InboxResponse, status_code=status.HTTP_201_CREATED)
async def create_inbox(
    data: InboxCreate,
    svc: InboxService = Depends(get_inbox_service),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可创建渠道")
    return await svc.create_inbox(data)


@router.get("/inboxes/{inbox_id}", response_model=InboxResponse)
async def get_inbox(
    inbox_id: str,
    svc: InboxService = Depends(get_inbox_service),
    _: User = Depends(get_current_user),
):
    inbox = await svc.get_inbox(inbox_id)
    if not inbox:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="渠道不存在")
    return inbox


@router.patch("/inboxes/{inbox_id}", response_model=InboxResponse)
async def update_inbox(
    inbox_id: str,
    data: InboxUpdate,
    svc: InboxService = Depends(get_inbox_service),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可修改渠道")
    inbox = await svc.update_inbox(inbox_id, data)
    if not inbox:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="渠道不存在")
    return inbox


@router.delete("/inboxes/{inbox_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inbox(
    inbox_id: str,
    svc: InboxService = Depends(get_inbox_service),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可删除渠道")
    deleted = await svc.delete_inbox(inbox_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="渠道不存在")
