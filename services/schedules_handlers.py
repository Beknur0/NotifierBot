from typing import TYPE_CHECKING
import asyncio

from aiogram import Bot


from database import new_session
from repositories.notifications import NotificationsRepository

if TYPE_CHECKING:
    from apscheduler.events import JobExecutionEvent


_bot: Bot = None


def init_bot(bot_instance):
    global _bot
    _bot = bot_instance


def listener_wrapper(event):
    try:
        loop = asyncio.get_running_loop()
        asyncio.run_coroutine_threadsafe(delete_missed_job(event), loop)
    except RuntimeError:
        pass


async def test_method(user_id: int, job_id: str, type: str):
    await _bot.send_message(
        user_id, text=f"Тестовый запуск типа {type} с job_id: {job_id} успешен"
    )
    if type in ["exact", "timer"]:
        async with new_session() as session:
            await NotificationsRepository.delete_by_job_id(job_id, session)


async def delete_missed_job(event: "JobExecutionEvent") -> None:
    job_id = event.job_id
    async with new_session() as session:
        await NotificationsRepository.delete_by_job_id(job_id, session)
