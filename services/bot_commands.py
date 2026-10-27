from aiogram.types import BotCommand


def get_commands() -> list[BotCommand]:
    return [
        BotCommand(command="start", description="Главное меню бота"),
    ]
