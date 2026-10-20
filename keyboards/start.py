from typing import TYPE_CHECKING

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_start_keyboard():
    buttons = [
        [
            InlineKeyboardButton(
                text="➕ Создать напоминание", callback_data="add_new_event"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📋 Мои напоминания", callback_data="my_notifications"
            ),
        ],
        # [
        #     InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
        # ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
