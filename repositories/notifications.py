from sqlalchemy import delete, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.notifications import NotificationsModel


class NotificationsRepository:
    @classmethod
    async def add_notification(cls, data: dict, session: AsyncSession):
        notification = NotificationsModel(**data)
        session.add(notification)
        await session.commit()
        await notification

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
        query = (
            select(NotificationsModel)
            .where(NotificationsModel.user_id == user_id)
            .order_by(desc(NotificationsModel.created_at))
        )
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

    @classmethod
    async def get_notification_by_job_id(
        cls,
        job_id: str,
        session: AsyncSession,
    ):
        stmt = select(NotificationsModel).where(NotificationsModel.job_id == job_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    @classmethod
    async def update_notification(
        cls,
        id: int,
        dictionary: dict,
        session: AsyncSession,
    ):
        stmt = (
            update(NotificationsModel)
            .where(NotificationsModel.id == id)
            .values(**dictionary)
        )
        await session.execute(stmt)
        await session.commit()

        stmt = select(NotificationsModel).where(NotificationsModel.id == id)
        result = await session.execute(stmt)
        return result.scalars().first()
