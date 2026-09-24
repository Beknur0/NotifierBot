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
    async def delete_executed_job(cls, job_id: str, session: AsyncSession):
        query = delete(NotificationsModel).where(NotificationsModel.job_id == job_id)
        await session.execute(query)
        await session.commit()