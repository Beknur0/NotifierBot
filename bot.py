import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from middlewares.db_session import DbSessionMiddleware
from database import new_session
from handlers import (
    start,
    cancel,
    new,
    edit,
    list,
)
from scheduler import scheduler
from services.schedules_handlers import init_bot
from services.bot_commands import get_commands


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    bot = Bot(
        token=config.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    dp.update.middleware(DbSessionMiddleware(session_pool=new_session))

    dp.include_routers(
        start.router,
        cancel.router,
        new.router,
        edit.router,
        list.router,
    )
    await bot.set_my_commands(get_commands())

    init_bot(bot)

    @dp.startup()
    async def on_startup(bot: Bot):
        scheduler.start()
        print("🔗 Scheduler starts 🔗")

    @dp.shutdown()
    async def on_shutdown():
        scheduler.shutdown()
        print("📌 Scheduler shutdowns 📌")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
