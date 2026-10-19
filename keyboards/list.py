from typing import TYPE_CHECKING
import numpy as np

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

if TYPE_CHECKING:
    from handlers.list import NotificationsListCallback
    from models.notifications import NotificationsModel


def get_back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ]
    )


def get_notifications_list_keyboard(
    callback_fabric: NotificationsListCallback,
    notifications: list[NotificationsModel],
    count: int,
):
    all_page = (len(notifications) // 5) + (1 if len(notifications) % 5 != 0 else 0)
    if count == 0:
        needable = notifications
    elif count == 1:
        needable = notifications[:5]
    elif count == all_page:
        needable = notifications[-(len(notifications) % 5) :]
    else:
        needable == notifications[count * 5 - 5, count * 5]

    btns = [
        [
            InlineKeyboardButton(
                text=f"{notification.title}",
                callback_data=callback_fabric(
                    action="select", value=notification.id
                ).pack(),
            )
        ]
        for notification in needable
    ]
    nav = [
        InlineKeyboardButton(
            text="<",
            callback_data=callback_fabric(action="change", value=-1, now=count).pack(),
        ),
        InlineKeyboardButton(text=f"{count}", callback_data=" "),
        InlineKeyboardButton(
            text=">",
            callback_data=callback_fabric(action="change", value=1, now=count).pack(),
        ),
    ]

    add_and_menu = [
        InlineKeyboardButton(
            text="➕ Создать напоминание", callback_data="add_new_event"
        ),
        InlineKeyboardButton(text="🏠 Меню", callback_data="cancel"),
    ]
    if count != 0:
        btns.append(nav)
    btns.append(add_and_menu)
    return InlineKeyboardMarkup(inline_keyboard=btns)


def get_notification_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать", callback_data="edit_notification"
                ),
                InlineKeyboardButton(
                    text="⏸ Приостановить", callback_data="pause_notification"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить", callback_data="delete_notification"
                ),
                InlineKeyboardButton(text="◀️ Назад", callback_data="back"),
            ],
        ]
    )


def get_editing_fields_keyboard(title: str, time: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📝 Название: {title}", callback_data="editTitleCreated"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"🕘 Время: {time}", callback_data="editTimeCreated"
                ),
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="back"),
            ],
        ]
    )
