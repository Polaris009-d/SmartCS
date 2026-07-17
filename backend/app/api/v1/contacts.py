"""
联系人 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.deps import get_current_user, get_contact_service
from app.models.user import User
from app.schemas.contact import ContactUpdate, ContactResponse
from app.schemas.common import PaginatedResponse
from app.services.contact_service import ContactService

router = APIRouter()


@router.get("/contacts", response_model=PaginatedResponse[ContactResponse])
async def list_contacts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    svc: ContactService = Depends(get_contact_service),
    _: User = Depends(get_current_user),
):
    contacts, total = await svc.list_contacts(page=page, page_size=page_size)
    return PaginatedResponse.from_items(
        items=[ContactResponse.model_validate(c) for c in contacts],
        total=total, page=page, page_size=page_size,
    )


@router.get("/contacts/search", response_model=list[ContactResponse])
async def search_contacts(
    q: str = Query(..., min_length=1),
    svc: ContactService = Depends(get_contact_service),
    _: User = Depends(get_current_user),
):
    contacts = await svc.search_contacts(q)
    return [ContactResponse.model_validate(c) for c in contacts]


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
    svc: ContactService = Depends(get_contact_service),
    _: User = Depends(get_current_user),
):
    contact = await svc.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="联系人不存在")
    return contact


@router.patch("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    data: ContactUpdate,
    svc: ContactService = Depends(get_contact_service),
    _: User = Depends(get_current_user),
):
    contact = await svc.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="联系人不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(contact, key, value)
    await svc.db.flush()
    return contact
