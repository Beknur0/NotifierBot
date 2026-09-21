from typing import TYPE_CHECKING

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

if TYPE_CHECKING:
    pass


def get_back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="editBack")]]
    )


def get_edit_fields_keyboard(title: str, type: str, time: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📝 Название: {title}", callback_data="editTitle"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"⏱ Тип повторения: {type}", callback_data="editRepeatType"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"🕘 Время: {time}", callback_data="editTime"
                ),
            ],
        ]
    )
