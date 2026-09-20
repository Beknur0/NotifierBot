from typing import TYPE_CHECKING

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

if TYPE_CHECKING:
    from handlers.new import (
        RepeatTypeCallback,
        TimeCallback,
        TimerCallback,
        WeekdaysCallback,
    )


def get_cancel_keyboard():  # callback: BackCallback):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
            ]  # callback.pack())]
        ]
    )


def get_repeat_type_keyboard(callback_fabric: RepeatTypeCallback):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Конкретная дата",
                    callback_data=callback_fabric(type="exact").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏳ Через промежуток",
                    callback_data=callback_fabric(type="timer").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔁 Дни недели",
                    callback_data=callback_fabric(type="week").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔁 Каждый месяц",
                    callback_data=callback_fabric(type="month").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔁 Каждый год",
                    callback_data=callback_fabric(type="year").pack(),
                )
            ],
        ]
    )


def get_select_time_keyboard(
    callback_fabric: TimeCallback,
    hour: str,
    minute: str,
):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔼",
                    callback_data=callback_fabric(
                        unit="hour", action="change", value=1, hour=hour, minute=minute
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="🔼",
                    callback_data=callback_fabric(
                        unit="minute",
                        action="change",
                        value=1,
                        hour=hour,
                        minute=minute,
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="+5",
                    callback_data=callback_fabric(
                        unit="minute",
                        action="change",
                        value=5,
                        hour=hour,
                        minute=minute,
                    ).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=hour, callback_data=callback_fabric(action="ignore").pack()
                ),
                InlineKeyboardButton(
                    text=minute, callback_data=callback_fabric(action="ignore").pack()
                ),
                InlineKeyboardButton(
                    text="+10",
                    callback_data=callback_fabric(
                        unit="minute",
                        action="change",
                        value=10,
                        hour=hour,
                        minute=minute,
                    ).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔽",
                    callback_data=callback_fabric(
                        unit="hour", action="change", value=-1, hour=hour, minute=minute
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="🔽",
                    callback_data=callback_fabric(
                        unit="minute",
                        action="change",
                        value=-1,
                        hour=hour,
                        minute=minute,
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="+30",
                    callback_data=callback_fabric(
                        unit="minute",
                        action="change",
                        value=30,
                        hour=hour,
                        minute=minute,
                    ).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✔️ Выбрать",
                    callback_data=callback_fabric(
                        action="finish", hour=hour, minute=minute
                    ).pack(),
                )
            ],
        ]
    )


def get_timer_keyboard(callback_fabric: TimerCallback):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="5м", callback_data=callback_fabric(value="5 мин").pack()
                ),
                InlineKeyboardButton(
                    text="15м", callback_data=callback_fabric(value="15 мин").pack()
                ),
                InlineKeyboardButton(
                    text="30м", callback_data=callback_fabric(value="30 мин").pack()
                ),
            ],
            [
                InlineKeyboardButton(
                    text="1ч", callback_data=callback_fabric(value="1 час").pack()
                ),
                InlineKeyboardButton(
                    text="3ч", callback_data=callback_fabric(value="3 час").pack()
                ),
                InlineKeyboardButton(
                    text="6ч", callback_data=callback_fabric(value="6 час").pack()
                ),
            ],
            [
                InlineKeyboardButton(
                    text="12ч", callback_data=callback_fabric(value="12 час").pack()
                ),
                InlineKeyboardButton(
                    text="1д", callback_data=callback_fabric(value="1 день").pack()
                ),
                InlineKeyboardButton(
                    text="Своё ✏️", callback_data=callback_fabric(value="own").pack()
                ),
            ],
        ]
    )


def get_weekdays_keyboard(callback_fabric: WeekdaysCallback, days: dict[int, bool]):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Пн{" ✅" if days[1] else " ▫️"}",
                    callback_data=callback_fabric(day=1, action="switch").pack(),
                ),
                InlineKeyboardButton(
                    text=f"Вт{" ✅" if days[2] else " ▫️"}",
                    callback_data=callback_fabric(day=2, action="switch").pack(),
                ),
                InlineKeyboardButton(
                    text=f"Ср{" ✅" if days[3] else " ▫️"}",
                    callback_data=callback_fabric(day=3, action="switch").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"Чт{" ✅" if days[4] else " ▫️"}",
                    callback_data=callback_fabric(day=4, action="switch").pack(),
                ),
                InlineKeyboardButton(
                    text=f"Пт{" ✅" if days[5] else " ▫️"}",
                    callback_data=callback_fabric(day=5, action="switch").pack(),
                ),
                InlineKeyboardButton(
                    text=f"Сб{" ✅" if days[6] else " ▫️"}",
                    callback_data=callback_fabric(day=6, action="switch").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Убрать все",
                    callback_data=callback_fabric(action="remove_all").pack(),
                ),
                InlineKeyboardButton(
                    text=f"Вс{" ✅" if days[7] else " ▫️"}",
                    callback_data=callback_fabric(day=7, action="switch").pack(),
                ),
                InlineKeyboardButton(
                    text="Выбрать все",
                    callback_data=callback_fabric(action="select_all").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Готово",
                    callback_data=callback_fabric(action="finish").pack(),
                ),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
            ],
        ]
    )


def get_confirm_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Сохранить", callback_data="confirm"),
                InlineKeyboardButton(text="✏️ Изменить", callback_data="change"),
            ]
        ]
    )
