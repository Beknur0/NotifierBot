from datetime import date, datetime

from aiogram import F, Bot, Router
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from sqlalchemy.ext.asyncio import AsyncSession

from models.notifications import NotificationsModel
from repositories.notifications import NotificationsRepository
from handlers import new
from keyboards import service, list, start
from keyboards import new as new_kb
from services import scheduler


class PagesStates(StatesGroup):
    waiting_selection = State()
    waiting_editing_field = State()
    waiting_title_editing = State()
    waiting_date = State()
    waiting_time = State()
    waiting_timer = State()
    waiting_own_timer = State()


class NotificationsListCallback(CallbackData, prefix="list"):
    action: str
    value: int
    now: int | None = None


router = Router()


# ========================== Notifications List Process ==========================
@router.callback_query(StateFilter(None), F.data == "my_notifications")
async def process_my_list(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    await state.set_state(PagesStates.waiting_selection)
    all_data = await NotificationsRepository.get_all_notifications_by_user_id(
        callback.from_user.id, session
    )
    await state.update_data(all_data=all_data)
    if len(all_data) <= 5:
        markup = list.get_notifications_list_keyboard(
            NotificationsListCallback, all_data, 0
        )
    else:
        markup = list.get_notifications_list_keyboard(
            NotificationsListCallback, all_data, 1
        )
    msg = await callback.message.edit_text("📋 Ваши напоминания:", reply_markup=markup)
    await state.update_data(bot_msg=msg.message_id)


# ========================== Going to Next Pages and Showing Selected Notification ==========================
@router.callback_query(
    PagesStates.waiting_selection, NotificationsListCallback.filter()
)
async def process_list(
    callback: CallbackQuery,
    callback_data: NotificationsListCallback,
    state: FSMContext,
    session: AsyncSession,
):
    data = await state.get_data()
    all_data = data.get("all_data")
    if callback_data.action == "change":
        all_page = (len(all_data) // 5) + (1 if len(all_data) % 5 != 0 else 0)
        new_id = ((callback_data.now + callback_data.value - 1) % all_page) + 1
        await callback.message.edit_reply_markup(
            reply_markup=list.get_notifications_list_keyboard(
                NotificationsListCallback, all_data, new_id
            )
        )
    else:
        notification = await NotificationsRepository.get_notification_by_id(
            callback_data.value, session
        )
        await go_to_notification_page(callback, state, notification)


async def go_to_notification_page(
    callback: CallbackQuery | None,
    state: FSMContext,
    notification: NotificationsModel,
    message: Message | None = None,
):
    typ, vremiya = get_typ_vremiya(data=notification)
    text = get_prettified_print(notification, typ, vremiya)
    await state.update_data(
        selected_notification=notification, typ=typ, vremiya=vremiya
    )
    await state.set_state(None)
    if not message:
        msg = await callback.message.edit_text(
            text=text, reply_markup=list.get_notification_keyboard()
        )
    else:
        msg = await message.answer(
            text=text, reply_markup=list.get_notification_keyboard()
        )
    await state.update_data(bot_msg=msg.message_id)


# ========================== Output Generating Functions ==========================
def get_prettified_print(notification: NotificationsModel, typ: str, vremiya: str):
    return f"""
📌 {notification.title}

{"⏱ Повторение:":<18} {typ}
{"🕘 Время:":<25} {vremiya}
{"📅 Создано:":<23} {notification.created_at.strftime("%H:%M %d.%m.%Y")}
{"📊 Статус:":<25} {"🟢 Активно" if notification.is_active else "🔴 Не активно"}
"""


def get_typ_vremiya(data: NotificationsModel):
    if data.repeat_type == "exact":
        typ = "Конкретная дата"
        vremiya = f"{data.time} {data.date.strftime('%d.%m.%Y')}"
    elif data.repeat_type == "timer":
        typ = "Через промежуток"
        vremiya = f"{data.timer_str}"
    elif data.repeat_type == "week":
        typ = "Дни недели"
        vremiya = f"{data.time} {new.get_string_weekdays(data.weekdays)}"
    elif data.repeat_type == "month":
        typ = "Каждый месяц"
        vremiya = f"{data.time} " + (
            f"каждое {data.month_day} число"
            if data.month_day.isdigit()
            else f"последний день месяца"
        )
    elif data.repeat_type == "year":
        typ = "Каждый год"
        vremiya = f"{data.time} {data.year_month}"
    return typ, vremiya


# ========================== Selecting Editing Field ==========================
@router.callback_query(StateFilter(None), F.data == "edit_notification")
async def process_editing(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    notification: NotificationsModel = data.get("selected_notification")
    vremiya = data.get("vremiya")
    await state.set_state(PagesStates.waiting_editing_field)
    msg = await callback.message.edit_text(
        "✏️ Что хотите изменить?",
        reply_markup=list.get_editing_fields_keyboard(
            title=notification.title, time=vremiya
        ),
    )
    await state.update_data(bot_msg=msg.message_id)


# ========================== Title Editing Process ==========================
@router.callback_query(PagesStates.waiting_editing_field, F.data == "editTitleCreated")
async def process_title_editing(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    notification: NotificationsModel = data.get("selected_notification")
    await state.set_state(PagesStates.waiting_title_editing)
    msg = await callback.message.edit_text(
        f"✏️ Текущее название: {notification.title} \n\n Введите новое название или описание напоминания",
        reply_markup=list.get_back_keyboard(),
    )
    await state.update_data(bot_msg=msg.message_id)


@router.message(PagesStates.waiting_title_editing)
async def edit_new_title_process(
    message: Message, state: FSMContext, bot: Bot, session: AsyncSession
):
    # await state.update_data(title=message.text)
    data = await state.get_data()
    notification: NotificationsModel = data.get("selected_notification")
    bot_msg = data.get("bot_msg")
    new_notification = await NotificationsRepository.update_notification(
        id=notification.id, dictionary={"title": message.text}, session=session
    )
    await go_to_notification_page(None, state, new_notification, message)

    try:
        await message.delete()
    except Exception:
        pass
    if bot_msg:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=bot_msg)
        except Exception:
            pass


# ========================== Time Editing Process ==========================
@router.callback_query(PagesStates.waiting_editing_field, F.data == "editTimeCreated")
async def process_time_editing(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    data = await state.get_data()
    notification: NotificationsModel = data.get("selected_notification")
    if notification.repeat_type == "exact":
        await state.update_data(for_time="date")
        await state.set_state(PagesStates.waiting_date)
        msg = await callback.message.edit_text(
            f"✏️ Текущая дата: {notification.date.strftime('%d.%m.%Y')} \n\n Выберите дату",
            reply_markup=await SimpleCalendar(locale="ru").start_calendar(),
        )
    elif notification.repeat_type == "timer":
        await state.update_data(for_time="timer_seconds")
        await state.set_state(PagesStates.waiting_timer)
        msg = await callback.message.edit_text(
            f"✏️ Текущее время напоминания: {notification.timer_str} \n\n Через сколько времени напомнить?",
            reply_markup=service.merge_keyboards(
                new_kb.get_timer_keyboard(new.TimerCallback),
                list.get_back_keyboard(),
            ),
        )
    # elif notification.repeat_type == "week":
    #     await state.set_state(new.NewNotification.waiting_weekdays)
    #     week_days = {
    #         1: False,
    #         2: False,
    #         3: False,
    #         4: False,
    #         5: False,
    #         6: False,
    #         7: False,
    #     }
    #     for day in notification.weekdays.split(", "):
    #         week_days[int(day)] == True
    #     msg = await callback.message.edit_text(
    #         f"✏️ Текущие дни недели: {new.get_string_weekdays(notification.weekdays)} \n\n Выберите дни недели",
    #         reply_markup=new_kb.get_weekdays_keyboard(new.WeekdaysCallback, week_days),
    #     )
    # elif notification.repeat_type == "month":
    #     await state.set_state(new.NewNotification.waiting_month_day)
    #     msg = await callback.message.edit_text(
    #         f"✏️ Текущий день месяца: {notification.month_day if notification.month_day.isdigit() else "последний день месяца"} \n\n Выберите в какой день месяца напоминать?",
    #         reply_markup=service.merge_keyboards(
    #             new_kb.get_month_day_keyboard(new.MonthDayCallback),
    #             list.get_back_keyboard(),
    #         ),
    #     )
    # elif notification.repeat_type == "year":
    #     await state.set_state(new.NewNotification.waiting_year_month)
    #     msg = await callback.message.edit_text(
    #         f"✏️ Текущая дата: {notification.year_month} \n\n Выберите в какой день и месяц напоминать?",
    #         reply_markup=service.merge_keyboards(
    #             new_kb.get_year_month_keyboard(
    #                 new.YearMonthCallback,
    #                 1,
    #                 new.months_names[1],
    #                 new.months_days[1],
    #             ),
    #             list.get_back_keyboard(),
    #         ),
    #     )
    await state.update_data(bot_msg=msg.message_id)


# ========================== Time Editing Exact Repeat Type ==========================
@router.callback_query(PagesStates.waiting_date, SimpleCalendarCallback.filter())
async def process_calendar(
    callback: CallbackQuery,
    callback_data: SimpleCalendarCallback,
    state: FSMContext,
):
    if callback_data.act == "CANCEL":
        await process_back_logic2(callback, state)
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
                f"✏️ Выберите дату",
                reply_markup=await SimpleCalendar(locale="ru").start_calendar(),
            )
            await state.update_data(bot_msg=msg.message_id)
            return

        await state.update_data(date=chosen_date)
        await state.set_state(PagesStates.waiting_time)
        msg = await callback.message.edit_text(
            f"📅 Вы выбрали дату: {chosen_date.strftime('%d.%m.%Y')} \n\n Выберите время",
            reply_markup=service.merge_keyboards(
                new_kb.get_select_time_keyboard(
                    new.TimeCallback, hour="00", minute="00"
                ),
                new_kb.get_cancel_keyboard(),
            ),
        )
        await state.update_data(bot_msg=msg.message_id)


# ========================== Time Editing Timer Repeat Type ==========================
@router.callback_query(PagesStates.waiting_timer, new.TimerCallback.filter())
async def process_timer(
    callback: CallbackQuery,
    callback_data: new.TimerCallback,
    state: FSMContext,
    session: AsyncSession,
):
    if callback_data.value != "own":
        data = await state.get_data()
        notification: NotificationsModel = data.get("selected_notification")
        col = data.get("for_time")
        dictionary = {
            col: new.to_seconds(callback_data.value),
        }
        await scheduler.update_exact_job(notification.job_id, dictionary)
        new_notification = await NotificationsRepository.update_notification(
            id=notification.id,
            dictionary={
                col: new.to_seconds(callback_data.value),
                "timer_str": callback_data.value,
            },
            session=session,
        )
        await state.update_data(selected_notification=new_notification)
        await go_to_notification_page(callback, state, new_notification)

    else:
        await state.set_state(PagesStates.waiting_own_timer)
        msg = await callback.message.edit_text(
            text=("""Введи время в формате:
"X год, Y месяц, Z неделя, N день, M час, K мин, V сек"
Например: 2 неделя, 1 час, 5 мин, 45 сек"""),
            reply_markup=new_kb.get_cancel_keyboard(),
        )
        await state.update_data(bot_msg=msg.message_id)


@router.message(PagesStates.waiting_own_timer)
async def process_own_timer(
    message: Message,
    state: FSMContext,
    bot: Bot,
    session: AsyncSession,
):
    if new.validate_time_format(message.text):
        sec = new.to_seconds(message.text)
        if sec != 0:
            await state.update_data(timer_seconds=sec)
            await state.update_data(timer_str=message.text)
            data = await state.get_data()
            bot_msg = data.get("bot_msg")
            notification: NotificationsModel = data.get("selected_notification")
            col = data.get("for_time")
            dictionary = {
                col: sec,
            }
            await scheduler.update_exact_job(notification.job_id, dictionary)
            new_notification = await NotificationsRepository.update_notification(
                id=notification.id,
                dictionary={
                    col: sec,
                    "timer_str": message.text,
                },
                session=session,
            )
            await state.update_data(selected_notification=new_notification)
            await go_to_notification_page(None, state, new_notification, message)

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


# ========================== Time Editing For Different Repeat Types ==========================
@router.callback_query(PagesStates.waiting_time, new.TimeCallback.filter())
async def process_time(
    callback: CallbackQuery,
    callback_data: new.TimeCallback,
    state: FSMContext,
    session: AsyncSession,
):
    if callback_data.action == "change":
        await new.update_time(callback, callback_data, state)
    else:
        data = await state.get_data()
        notification: NotificationsModel = data.get("selected_notification")
        col = data.get("for_time")
        dictionary = {
            col: data.get(col).strftime("%d.%m.%Y"),
            "time": f"{callback_data.hour}:{callback_data.minute}",
        }
        await scheduler.update_exact_job(notification.job_id, dictionary)
        new_notification = await NotificationsRepository.update_notification(
            id=notification.id,
            dictionary={
                col: data.get(col),
                "time": f"{callback_data.hour}:{callback_data.minute}",
            },
            session=session,
        )
        await state.update_data(selected_notification=new_notification)
        await go_to_notification_page(callback, state, new_notification)


# ========================== Processing Back Logics ==========================
@router.callback_query(PagesStates.waiting_editing_field, F.data == "back")
async def process_back_logic(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    notification = data.get("selected_notification")
    await go_to_notification_page(callback, state, notification)


@router.callback_query(StateFilter(None), F.data == "back")
async def process_back_logic3(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        f"👋 Привет, {callback.from_user.full_name}! \n Я твой личный помощник для напоминаний. \n\n Выберите действие:",
        reply_markup=start.get_start_keyboard(),
    )


@router.callback_query(StateFilter("*"), F.data == "back")
async def process_back_logic2(callback: CallbackQuery, state: FSMContext):
    await process_editing(callback, state)
