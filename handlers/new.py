from datetime import date, datetime
import re

from aiogram import Router, F
from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackData
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import (
    service,
    start,
    new,
)
from repositories.users import UsersRepository
from repositories.notifications import NotificationsRepository
from services import scheduler

router = Router()


# ========================== FSM ==========================
class NewNotification(StatesGroup):
    waiting_title = State()
    waiting_repeat_type = State()
    waiting_date = State()
    waiting_time = State()
    waiting_timer = State()
    waiting_own_timer = State()
    waiting_weekdays = State()
    waiting_month_day = State()
    waiting_year_month = State()
    waiting_confirm = State()


# ========================== Callback Fabric ==========================
class RepeatTypeCallback(CallbackData, prefix="repeat_type"):
    type: str


class TimeCallback(CallbackData, prefix="time"):
    unit: str | None = None
    action: str
    value: int | None = None
    hour: str | None = None
    minute: str | None = None


class TimerCallback(CallbackData, prefix="timer"):
    value: str


class WeekdaysCallback(CallbackData, prefix="weekdays"):
    day: int | None = None
    action: str


class MonthDayCallback(CallbackData, prefix="month_day"):
    value: str


class YearMonthCallback(CallbackData, prefix="year_month"):
    action: str
    value: int
    now: int


# ========================== New Event Title ==========================
@router.callback_query(F.data == "add_new_event")
async def add_new_event(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NewNotification.waiting_title)
    msg = await callback.message.edit_text(
        '📝 Шаг 1 из 4 \n\n Введите название или описание напоминания. \n\n Например: "Выпить таблетки" или "Созвон с командой"',
        reply_markup=new.get_cancel_keyboard(),  # BackCallback(value="start")),
    )
    await state.update_data(bot_msg=msg.message_id)
    await callback.answer()


# ========================== Selection of Repeater Type ==========================
@router.message(NewNotification.waiting_title)
async def process_event_name(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    bot_msg = data.get("bot_msg")
    await state.update_data(title=message.text)
    await state.set_state(NewNotification.waiting_repeat_type)
    msg = await message.answer(
        f'✅ Записал: "{message.text}" \n\n ⏱ Шаг 2 из 4 \n\n Как часто напоминать?',
        reply_markup=service.merge_keyboards(
            new.get_repeat_type_keyboard(RepeatTypeCallback),
            new.get_cancel_keyboard(),
        ),
    )

    try:
        await message.delete()
    except Exception:
        pass
    if bot_msg:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=bot_msg)
        except Exception:
            pass
    await state.update_data(bot_msg=msg.message_id)


# ========================== Exact Repeater Type ==========================
@router.callback_query(
    NewNotification.waiting_repeat_type, RepeatTypeCallback.filter(F.type == "exact")
)
async def process_exact_type(
    callback: CallbackQuery,
    callback_data: RepeatTypeCallback,
    state: FSMContext,
):
    await state.update_data(repeat_type=callback_data.type)
    await state.set_state(NewNotification.waiting_date)
    msg = await callback.message.edit_text(
        "📅 Шаг 3.1 из 4 \n\n Выберите дату",
        reply_markup=await SimpleCalendar(locale="ru").start_calendar(),
    )
    await state.update_data(bot_msg=msg.message_id)


@router.callback_query(SimpleCalendarCallback.filter())
async def process_calendar(
    callback: CallbackQuery,
    callback_data: SimpleCalendarCallback,
    state: FSMContext,
):
    if callback_data.act == "CANCEL":
        await back_to(callback, state)
        return

    calendar = SimpleCalendar(locale="ru")
    selected, chosen_date = await calendar.process_selection(callback, callback_data)
    if selected:
        if isinstance(chosen_date, datetime):
            chosen_date = chosen_date.date()
        today = date.today()
        if chosen_date < today:
            await callback.answer(
                "❌ Нельзя выбрать прошедшую дату! Выберите другой день."
            )
            msg = await callback.message.edit_text(
                "📅 Шаг 3.1 из 4 \n\n Выберите дату",
                reply_markup=await SimpleCalendar(locale="ru").start_calendar(),
            )
            await state.update_data(bot_msg=msg.message_id)
            return

        await state.update_data(date=chosen_date)
        await state.set_state(NewNotification.waiting_time)
        msg = await callback.message.edit_text(
            f"📅 Вы выбрали дату: {chosen_date.strftime('%d.%m.%Y')} \n\n 🕒 Шаг 3.2 из 4 \n\n Выберите время",
            reply_markup=service.merge_keyboards(
                new.get_select_time_keyboard(TimeCallback, hour="00", minute="00"),
                new.get_cancel_keyboard(),
            ),
        )
        await state.update_data(bot_msg=msg.message_id)


# ========================== Timer Repeater Type ==========================
@router.callback_query(
    NewNotification.waiting_repeat_type, RepeatTypeCallback.filter(F.type == "timer")
)
async def process_timer_type(
    callback: CallbackQuery,
    callback_data: RepeatTypeCallback,
    state: FSMContext,
):
    await state.update_data(repeat_type=callback_data.type)
    await state.set_state(NewNotification.waiting_timer)
    msg = await callback.message.edit_text(
        "📅 Шаг 3 из 4 \n\n Через сколько времени напомнить?",
        reply_markup=service.merge_keyboards(
            new.get_timer_keyboard(TimerCallback), new.get_cancel_keyboard()
        ),
    )
    await state.update_data(bot_msg=msg.message_id)


def to_seconds(s: str):
    s = s.split(", ")

    units = {
        "сек": 1,
        "мин": 60,
        "час": 3600,
        "день": 86_400,
        "неделя": 604_800,
        "месяц": 2_592_000,
        "год": 31_536_000,
    }
    sec = 0
    for i in s:
        c, u = i.split(" ")
        sec += int(c) * units[u]
    return sec


@router.callback_query(NewNotification.waiting_timer, TimerCallback.filter())
async def process_timer(
    callback: CallbackQuery, callback_data: TimerCallback, state: FSMContext
):
    if callback_data.value != "own":
        await state.update_data(timer_seconds=to_seconds(callback_data.value))
        await state.update_data(timer_str=callback_data.value)
        await state.set_state(NewNotification.waiting_confirm)
        await confirmation_step(callback=callback, state=state)
    else:
        await state.set_state(NewNotification.waiting_own_timer)
        msg = await callback.message.edit_text(
            text=("""Введи время в формате:
"X год, Y месяц, Z неделя, N день, M час, K мин, V сек"
Например: 2 неделя, 1 час, 5 мин, 45 сек"""),
            reply_markup=new.get_cancel_keyboard(),
        )
        await state.update_data(bot_msg=msg.message_id)


def validate_time_format(text: str) -> bool:
    pattern = re.compile(
        r"^\d+\s+(год|месяц|неделя|день|час|мин|сек)"
        r"(?:,\s*\d+\s+(год|месяц|неделя|день|час|мин|сек))*$"
    )
    return bool(pattern.match(text))


@router.message(NewNotification.waiting_own_timer)
async def process_own_timer(message: Message, state: FSMContext, bot: Bot):
    if validate_time_format(message.text):
        sec = to_seconds(message.text)
        if sec != 0:
            await state.update_data(timer_seconds=sec)
            await state.update_data(timer_str=message.text)
            data = await state.get_data()
            bot_msg = data.get("bot_msg")
            await state.set_state(NewNotification.waiting_confirm)
            await confirmation_step(callback=None, state=state, message=message)

            if bot_msg:
                try:
                    await bot.delete_message(
                        chat_id=message.chat.id, message_id=bot_msg
                    )
                except Exception:
                    pass
    try:
        await message.delete()
    except Exception:
        pass


# ========================== Week Repeater Type ==========================
@router.callback_query(
    NewNotification.waiting_repeat_type, RepeatTypeCallback.filter(F.type == "week")
)
async def process_week_type(
    callback: CallbackQuery,
    callback_data: RepeatTypeCallback,
    state: FSMContext,
):
    await state.update_data(repeat_type=callback_data.type)
    await state.set_state(NewNotification.waiting_weekdays)
    week_days = {
        1: False,
        2: False,
        3: False,
        4: False,
        5: False,
        6: False,
        7: False,
    }
    await state.update_data(week_days=week_days)
    msg = await callback.message.edit_text(
        '📅 Шаг 3.1 из 4 \n\n Выберите дни недели (можно несколько). \n Нажимай на дни, потом нажми "Готово".',
        reply_markup=new.get_weekdays_keyboard(WeekdaysCallback, week_days),
    )
    await state.update_data(bot_msg=msg.message_id)


async def update_weekdays_keyboard(
    callback: CallbackQuery, state: FSMContext, week_days: dict
):
    await state.update_data(week_days=week_days)
    await callback.message.edit_reply_markup(
        reply_markup=new.get_weekdays_keyboard(WeekdaysCallback, week_days),
    )


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


@router.callback_query(NewNotification.waiting_weekdays, WeekdaysCallback.filter())
async def process_weekdays(
    callback: CallbackQuery, callback_data: WeekdaysCallback, state: FSMContext
):
    data = await state.get_data()
    week_days = data.get("week_days")
    if callback_data.action == "switch":
        week_days[callback_data.day] = not week_days[callback_data.day]
        await update_weekdays_keyboard(callback, state, week_days)
    elif callback_data.action == "remove_all":
        flag = False
        for i, j in week_days.items():
            if j:
                flag = True
            week_days[i] = False
        if flag:
            await update_weekdays_keyboard(callback, state, week_days)
    elif callback_data.action == "select_all":
        flag = False
        for i, j in week_days.items():
            if not j:
                flag = True
            week_days[i] = True
        if flag:
            await update_weekdays_keyboard(callback, state, week_days)
    elif callback_data.action == "finish":
        text = ""
        for i, j in week_days.items():
            if j:
                text += f"{i}, "
        text = text[:-2]
        if not text:
            await callback.answer("Нужно выбрать хотя бы один день недели")
            return
        await state.update_data(weekdays=text)
        await state.set_state(NewNotification.waiting_time)
        msg = await callback.message.edit_text(
            f"📅 Вы выбрали эти дни недели: {get_string_weekdays(text)} \n\n 🕒 Шаг 3.2 из 4 \n\n Выберите время",
            reply_markup=service.merge_keyboards(
                new.get_select_time_keyboard(TimeCallback, hour="00", minute="00"),
                new.get_cancel_keyboard(),
            ),
        )
        await state.update_data(bot_msg=msg.message_id)


# ========================== Month Repeater Type ==========================
@router.callback_query(
    NewNotification.waiting_repeat_type, RepeatTypeCallback.filter(F.type == "month")
)
async def process_week_type(
    callback: CallbackQuery,
    callback_data: RepeatTypeCallback,
    state: FSMContext,
):
    await state.update_data(repeat_type=callback_data.type)
    await state.set_state(NewNotification.waiting_month_day)
    msg = await callback.message.edit_text(
        "📅 Шаг 3.1 из 4 \n\n Выберите в какой день месяца напоминать?",
        reply_markup=service.merge_keyboards(
            new.get_month_day_keyboard(MonthDayCallback), new.get_cancel_keyboard()
        ),
    )
    await callback.answer()
    await state.update_data(bot_msg=msg.message_id)


@router.callback_query(NewNotification.waiting_month_day, MonthDayCallback.filter())
async def process_month_day(
    callback: CallbackQuery, callback_data: MonthDayCallback, state: FSMContext
):
    await state.update_data(month_day=callback_data.value)
    await state.set_state(NewNotification.waiting_time)
    s = callback_data.value
    if not s.isdigit():
        s = "Последний день месяца"
    msg = await callback.message.edit_text(
        f"📅 Вы выбрали это число месяца: {s} \n\n 🕒 Шаг 3.2 из 4 \n\n Выберите время",
        reply_markup=service.merge_keyboards(
            new.get_select_time_keyboard(TimeCallback, hour="00", minute="00"),
            new.get_cancel_keyboard(),
        ),
    )
    await state.update_data(bot_msg=msg.message_id)


# ========================== Year Repeater Type ==========================
@router.callback_query(
    NewNotification.waiting_repeat_type, RepeatTypeCallback.filter(F.type == "year")
)
async def process_week_type(
    callback: CallbackQuery,
    callback_data: RepeatTypeCallback,
    state: FSMContext,
):
    await state.update_data(repeat_type=callback_data.type)
    await state.set_state(NewNotification.waiting_year_month)
    msg = await callback.message.edit_text(
        "📅 Шаг 3.1 из 4 \n\n Выберите в какой день и месяц напоминать?",
        reply_markup=service.merge_keyboards(
            new.get_year_month_keyboard(
                YearMonthCallback, 1, months_names[1], months_days[1]
            ),
            new.get_cancel_keyboard(),
        ),
    )
    await state.update_data(bot_msg=msg.message_id)


months_names = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь",
}
months_days = {
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31,
}


@router.callback_query(NewNotification.waiting_year_month, YearMonthCallback.filter())
async def process_year_month(
    callback: CallbackQuery, callback_data: YearMonthCallback, state: FSMContext
):
    if callback_data.action == "change":
        new_id = ((callback_data.now + callback_data.value - 1) % 12) + 1
        await callback.message.edit_reply_markup(
            reply_markup=service.merge_keyboards(
                new.get_year_month_keyboard(
                    callback_fabric=YearMonthCallback,
                    id=new_id,
                    month=months_names[new_id],
                    days=months_days[new_id],
                ),
                new.get_cancel_keyboard(),
            )
        )
    else:
        s = f"{str(callback_data.value).zfill(2)}.{str(callback_data.now).zfill(2)}"
        await state.update_data(year_month=s)
        await state.set_state(NewNotification.waiting_time)
        msg = await callback.message.edit_text(
            f"📅 Вы выбрали дату: {s} \n\n 🕒 Шаг 3.2 из 4 \n\n Выберите время",
            reply_markup=service.merge_keyboards(
                new.get_select_time_keyboard(TimeCallback, hour="00", minute="00"),
                new.get_cancel_keyboard(),
            ),
        )
        await state.update_data(bot_msg=msg.message_id)


# ========================== Time ==========================
@router.callback_query(NewNotification.waiting_time, TimeCallback.filter())
async def process_time(
    callback: CallbackQuery, callback_data: TimeCallback, state: FSMContext
):
    if callback_data.action == "change":
        await update_time(callback, callback_data, state)
    else:
        await state.update_data(time=f"{callback_data.hour}:{callback_data.minute}")
        await state.set_state(NewNotification.waiting_confirm)
        await confirmation_step(callback=callback, state=state)


async def update_time(
    callback: CallbackQuery, callback_data: TimeCallback, state: FSMContext
):
    data = await state.get_data()

    hour = callback_data.hour
    minute = callback_data.minute

    if callback_data.unit == "hour":
        hour = str((int(hour) + callback_data.value) % 24).zfill(2)
    elif callback_data.unit == "minute":
        minute = str((int(minute) + callback_data.value) % 60).zfill(2)

    if data["repeat_type"] == "exact":
        vremiya = f"📅 Вы выбрали дату: {data["date"].strftime('%d.%m.%Y')}"
    elif data["repeat_type"] == "week":
        vremiya = (
            f"📅 Вы выбрали эти дни недели: {get_string_weekdays(data["weekdays"])}"
        )
    elif data["repeat_type"] == "month":
        vremiya = f"📅 Вы выбрали это число месяца: {data["month_day"] if data["month_day"].isdigit() else "Последний день месяца"}"
    elif data["repeat_type"] == "year":
        vremiya = f"📅 Вы выбрали дату: {data["year_month"]}"

    msg = await callback.message.edit_text(
        f"{vremiya} \n\n 🕒 Шаг 3.2 из 4 \n\n Выберите время",
        reply_markup=service.merge_keyboards(
            new.get_select_time_keyboard(TimeCallback, hour=hour, minute=minute),
            new.get_cancel_keyboard(),
        ),
    )
    await state.update_data(bot_msg=msg.message_id)


# ========================== Confirmation Step ==========================
def get_typ_vremiya(data: dict):
    if data["repeat_type"] == "exact":
        typ = "Конкретная дата"
        vremiya = f"{data["time"]} {data["date"].strftime('%d.%m.%Y')}"
    elif data["repeat_type"] == "timer":
        typ = "Через промежуток"
        vremiya = f"{data["timer_str"]}"
    elif data["repeat_type"] == "week":
        typ = "Дни недели"
        vremiya = f"{data["time"]} {get_string_weekdays(data["weekdays"])}"
    elif data["repeat_type"] == "month":
        typ = "Каждый месяц"
        vremiya = f"{data["time"]} " + (
            f"каждое {data["month_day"]} число"
            if data["month_day"].isdigit()
            else f"последний день месяца"
        )
    elif data["repeat_type"] == "year":
        typ = "Каждый год"
        vremiya = f"{data["time"]} {data["year_month"]}"
    return typ, vremiya


async def confirmation_step(
    callback: CallbackQuery | None, state: FSMContext, message: Message | None = None
):
    data = await state.get_data()
    typ, vremiya = get_typ_vremiya(data)
    text = f"""📋 Шаг 4 из 4 - Проверьте данные:
    
{"📌 Название:":<18} {data["title"]}
{"⏱ Тип:":<25} {typ}
{"🕘 Время:":<21} {vremiya}
{"📊 Статус:":<22} Активно
        
Всё верно?"""

    if callback:
        msg = await callback.message.edit_text(
            text=text,
            reply_markup=service.merge_keyboards(
                new.get_confirm_keyboard(), new.get_cancel_keyboard(), horizontal=True
            ),
        )
    else:
        msg = await message.answer(
            text=text,
            reply_markup=service.merge_keyboards(
                new.get_confirm_keyboard(), new.get_cancel_keyboard(), horizontal=True
            ),
        )
    await state.update_data(bot_msg=msg.message_id)


# ========================== Confirm and Add to DB ==========================
@router.callback_query(NewNotification.waiting_confirm, F.data == "confirm")
async def process_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    if not await UsersRepository.get_user_by_id(callback.from_user.id, session):
        username = (
            callback.from_user.username
            if callback.from_user.username
            else callback.from_user.first_name
        )
        await UsersRepository.add_user(callback.from_user.id, username, session)

    data = await state.get_data()
    data_dict = {
        "user_id": callback.from_user.id,
        "title": data["title"],
        "repeat_type": data["repeat_type"],
        "date": data.get("date") if data.get("date") else None,
        "time": data.get("time") if data.get("time") else None,
        "timer_seconds": (
            data.get("timer_seconds") if data.get("timer_seconds") else None
        ),
        "weekdays": data.get("weekdays") if data.get("weekdays") else None,
        "month_day": data.get("month_day") if data.get("month_day") else None,
        "year_month": data.get("year_month") if data.get("year_month") else None,
    }
    if data_dict["repeat_type"] == "exact":
        job_id = await scheduler.add_exact_job(
            callback.from_user.id,
            data_dict["date"].strftime("%d.%m.%Y"),
            data_dict["time"],
        )
    elif data_dict["repeat_type"] == "timer":
        job_id = await scheduler.add_timer_job(
            callback.from_user.id, data_dict["timer_seconds"]
        )
    elif data_dict["repeat_type"] == "week":
        job_id = await scheduler.add_week_job(
            callback.from_user.id, data_dict["weekdays"], data_dict["time"]
        )
    elif data_dict["repeat_type"] == "month":
        job_id = await scheduler.add_month_job(
            callback.from_user.id, data_dict["month_day"], data_dict["time"]
        )
    elif data_dict["repeat_type"] == "year":
        job_id = await scheduler.add_year_job(
            callback.from_user.id, data_dict["year_month"], data_dict["time"]
        )
    data_dict["job_id"] = job_id

    await NotificationsRepository.add_notification(data_dict, session)
    await state.clear()
    await callback.message.edit_text("🎉 Напоминание создано!")
    await callback.answer()


# ========================== Cancel Logic ==========================
@router.callback_query(StateFilter("*"), F.data == "cancel")  # BackCallback.filter())
async def back_to(
    callback: CallbackQuery,
    # callback_data: BackCallback,
    state: FSMContext,
):
    current = await state.get_state()
    if current:
        await state.clear()
        await callback.message.edit_text(
            f"👋 Привет, {callback.from_user.full_name}! \n Я твой личный помощник для напоминаний. \n\n Выберите действие:",
            reply_markup=start.get_start_keyboard(),
        )
    await callback.answer()


# ========================== Message Delete Logic ==========================
@router.message(StateFilter(NewNotification))
async def delete_messages(message: Message):
    try:
        await message.delete()
    except Exception:
        pass
