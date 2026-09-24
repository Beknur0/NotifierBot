from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ThreadPoolExecutor

from config import config

jobstores = {
    "default": SQLAlchemyJobStore(
        url=config.db_url.replace("postgresql+asyncpg://", "postgresql://"),
        tablename="apscheduler_jobs",
        tableschema=None,
    )
}

executors = {
    "default": AsyncIOExecutor(),
    "threadpool": ThreadPoolExecutor(10),
}

job_defaults = {
    "coalesce": True,  # объединять пропущенные запуски в один
    "max_instances": 1,  # максимум 1 экземпляр задачи одновременно
    "misfire_grace_time": 59,  # допустимое опоздание в секундах
}

scheduler = AsyncIOScheduler(jobstores=jobstores)


# Удаление задачи
# try:
#     scheduler.remove_job(job_id)
#     print(f"Задача {job_id} успешно удалена!")
#     # Здесь можно отправить сообщение пользователю в боте: "Напоминание отменено."
# except Exception as e:
#     # Ошибка может возникнуть, если задачи с таким ID уже нет
#     # (например, она уже сработала и удалилась сама)
#     print(f"Не удалось удалить задачу: {e}")


# # Пользователь решил изменить время или текст существующего напоминания
# job_id = f"reminder_{user_id}_1750000000"

# # Новые данные
# new_run_time = datetime(2026, 6, 2, 18, 0, 0)
# new_text = "Купить молоко и хлеб (изменено)"

# scheduler.add_job(
#     send_reminder,
#     trigger='date',
#     run_date=new_run_time,
#     args=[bot, user_id, new_text],
#     id=job_id,              # Тот же самый ID!
#     replace_existing=True   # <--- Перезапишет старую задачу
# )


# job_id = f"reminder_{user_id}_1750000000"
# new_run_time = datetime(2026, 6, 2, 20, 0, 0)

# scheduler.reschedule_job(
#     job_id=job_id,
#     trigger='date',
#     run_date=new_run_time
# )


# job_id = f"reminder_{user_id}_1750000000"

# scheduler.modify_job(
#     job_id=job_id,
#     args=[bot, user_id, "Новый текст напоминания"]  # Меняем аргументы функции
# )
