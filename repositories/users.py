from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from models.users import UsersModel


class UsersRepository:
    @classmethod
    async def get_user_by_id(cls, user_id: int, session: AsyncSession):
        data: UsersModel | None = await session.scalar(
            select(UsersModel).where(UsersModel.user_id == user_id)
        )
        return data

    @classmethod
    async def add_user(cls, user_id: int, username: str, session: AsyncSession):
        new_user = UsersModel(user_id=user_id, username=username)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
