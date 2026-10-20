from typing import TYPE_CHECKING
import asyncio

from aiogram import Bot


from database import new_session
from repositories.notifications import NotificationsRepository
from models.notifications import NotificationsModel

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


async def notifying_user(user_id: int, job_id: str, type: str):
    async with new_session() as session:
        notification: NotificationsModel = (
            await NotificationsRepository.get_notification_by_job_id(job_id, session)
        )
    typ, vremiya = get_typ_vremiya(notification)
    text = f"""
🔔 Напоминание! 🔔

📌 {notification.title}
🕘 {vremiya} · {typ}
"""
    await _bot.send_message(
        user_id,
        text=text,
    )


def get_typ_vremiya(data: NotificationsModel):
    if data.repeat_type == "exact":
        typ = "Конкретная дата"
        vremiya = f"{data.time} {data.date.strftime('%d.%m.%Y')}"
        return typ, vremiya
    elif data.repeat_type == "timer":
        typ = "Через промежуток"
        vremiya = f"{data.timer_str}"
        return typ, vremiya
    elif data.repeat_type == "week":
        typ = "Дни недели"
        vremiya = f"{data.time} {get_string_weekdays(data.weekdays)}"
        return typ, vremiya
    elif data.repeat_type == "month":
        typ = "Каждый месяц"
        vremiya = f"{data.time} " + (
            f"Каждое {data.month_day} число"
            if data.month_day.isdigit()
            else f"Последний день месяца"
        )
        return typ, vremiya
    elif data.repeat_type == "year":
        typ = "Каждый год"
        vremiya = f"{data.time} {data.year_month}"
        return typ, vremiya


def get_string_weekdays(text: str):
    text = list(text)
    string = {
        "1": "Пн",
        "2": "Вт",
        "3": "Ср",
        "4": "Чт",
        "5": "Пт",
        "6": "Сб",
        "7": "Вс",
    }
    for i in range(len(text)):
        if text[i] in string:
            text[i] = string[text[i]]
    return "".join(text)


async def delete_missed_job(event: "JobExecutionEvent") -> None:
    job_id = event.job_id
    async with new_session() as session:
        await NotificationsRepository.delete_by_job_id(job_id, session)
