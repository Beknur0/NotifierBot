from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.notifications import NotificationsModel

class NotificationsRepository:
    @classmethod
    async def add_notification(cls, data: dict, session: AsyncSession):
        new_user = NotificationsModel(**data)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)