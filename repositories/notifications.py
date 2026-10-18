from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.notifications import NotificationsModel


class NotificationsRepository:
    @classmethod
    async def add_notification(cls, data: dict, session: AsyncSession):
        new_user = NotificationsModel(**data)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

    @classmethod
    async def delete_by_job_id(cls, job_id: str, session: AsyncSession):
        query = delete(NotificationsModel).where(NotificationsModel.job_id == job_id)
        await session.execute(query)
        await session.commit()

    @classmethod
    async def get_all_notifications_by_user_id(
        cls,
        user_id: int,
        session: AsyncSession,
    ):
        query = select(NotificationsModel).where(NotificationsModel.user_id == user_id)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_notification_by_id(
        cls,
        id: int,
        session: AsyncSession,
    ):
        query = select(NotificationsModel).where(NotificationsModel.id == id)
        result = await session.execute(query)
        return result.scalars().first()
