"""
联系人服务
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.contact import Contact, ContactInbox
from app.schemas.contact import ContactCreate, ContactUpdate


class ContactService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_contacts(self, page: int = 1, page_size: int = 20) -> tuple[list[Contact], int]:
        count_q = select(func.count()).select_from(Contact)
        total = (await self.db.execute(count_q)).scalar() or 0

        q = select(Contact).order_by(Contact.last_activity_at.desc().nulls_last()).offset(
            (page - 1) * page_size
        ).limit(page_size)
        result = await self.db.execute(q)
        return list(result.scalars().all()), total

    async def get_contact(self, contact_id: str) -> Contact | None:
        result = await self.db.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        return result.scalar_one_or_none()

    async def search_contacts(self, query: str) -> list[Contact]:
        pattern = f"%{query}%"
        result = await self.db.execute(
            select(Contact).where(
                or_(
                    Contact.name.ilike(pattern),
                    Contact.email.ilike(pattern),
                    Contact.phone.ilike(pattern),
                )
            ).limit(20)
        )
        return list(result.scalars().all())

    async def find_or_create_contact(
        self, email: str | None, phone: str | None, name: str | None,
        inbox_id: str, source_id: str | None
    ) -> tuple[Contact, ContactInbox]:
        """
        查找或创建联系人 + ContactInbox 关联。
        优先通过 ContactInbox(source_id) 查找，其次 email/phone。
        """
        contact_inbox = None

        # 1. 通过 source_id + inbox_id 查找已有 ContactInbox
        if source_id:
            result = await self.db.execute(
                select(ContactInbox).where(
                    ContactInbox.inbox_id == inbox_id,
                    ContactInbox.source_id == source_id,
                )
            )
            contact_inbox = result.scalar_one_or_none()

        # 2. 通过 email 或 phone 查找已有 Contact
        contact = None
        if contact_inbox:
            result = await self.db.execute(
                select(Contact).where(Contact.id == contact_inbox.contact_id)
            )
            contact = result.scalar_one_or_none()
        elif email:
            result = await self.db.execute(
                select(Contact).where(Contact.email == email)
            )
            contact = result.scalar_one_or_none()
        elif phone:
            result = await self.db.execute(
                select(Contact).where(Contact.phone == phone)
            )
            contact = result.scalar_one_or_none()

        # 3. 创建新 Contact
        if not contact:
            contact = Contact(
                name=name, email=email, phone=phone
            )
            self.db.add(contact)
            await self.db.flush()

        # 4. 创建 ContactInbox 关联
        if not contact_inbox:
            contact_inbox = ContactInbox(
                contact_id=contact.id,
                inbox_id=inbox_id,
                source_id=source_id or str(uuid.uuid4()),
                pubsub_token=str(uuid.uuid4()),
            )
            self.db.add(contact_inbox)
            await self.db.flush()

        return contact, contact_inbox
