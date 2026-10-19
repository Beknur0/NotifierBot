from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_REMOVED

from config import config
from services.schedules_handlers import listener_wrapper

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

scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone="Asia/Yekaterinburg",
)

scheduler.add_listener(listener_wrapper, EVENT_JOB_REMOVED)
