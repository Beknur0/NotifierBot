from aiogram import Router, F
from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackData
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from . import new as new_hand
from keyboards import (
    service,
    edit,
    new as new_kb,
)

router = Router()


# ========================== FSM ==========================
class EditNotification(StatesGroup):
    waiting_edit_field = State()
    waiting_edit_title = State()
    waiting_edit_repeat_type = State()


# ========================== Available Fields to Edit ==========================
@router.callback_query(new_hand.NewNotification.waiting_confirm, F.data == "edit")
async def edit_processing(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(EditNotification.waiting_edit_field)
    typ, vremiya = new_hand.get_typ_vremiya(data)
    msg = await callback.message.edit_text(
        "✏️ Что хотите изменить?",
        reply_markup=service.merge_keyboards(
            edit.get_edit_fields_keyboard(data["title"], typ, vremiya),
            edit.get_back_keyboard(),
        ),
    )
    await state.update_data(bot_msg=msg.message_id)


# ========================== Title Editing ==========================
@router.callback_query(EditNotification.waiting_edit_field, F.data == "editTitle")
async def edit_title_process(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(EditNotification.waiting_edit_title)
    msg = await callback.message.edit_text(
        f"✏️ Текущее название: {data["title"]} \n\n Введите новое название или описание напоминания",
        reply_markup=edit.get_back_keyboard(),
    )
    await state.update_data(bot_msg=msg.message_id)


@router.message(EditNotification.waiting_edit_title)
async def edit_new_title_process(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(title=message.text)
    data = await state.get_data()
    bot_msg = data.get("bot_msg")
    await state.set_state(new_hand.NewNotification.waiting_confirm)
    await new_hand.confirmation_step(None, state, message)

    try:
        await message.delete()
    except Exception:
        pass
    if bot_msg:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=bot_msg)
        except Exception:
            pass


# ========================== Repeat Type Editing ==========================
@router.callback_query(EditNotification.waiting_edit_field, F.data == "editRepeatType")
async def edit_repeat_type_process(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(new_hand.NewNotification.waiting_repeat_type)
    msg = await callback.message.edit_text(
        f"✏️ Текущий тип повторения: {data["repeat_type"]} \n\n Выберите новый тип повторения",
        reply_markup=service.merge_keyboards(
            new_kb.get_repeat_type_keyboard(new_hand.RepeatTypeCallback),
            edit.get_back_keyboard(),
        ),
    )
    await state.update_data(bot_msg=msg.message_id)


# ========================== Time Type Editing ==========================
@router.callback_query(EditNotification.waiting_edit_field, F.data == "editTime")
async def edit_time_process(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data["repeat_type"] == "exact":
        await state.set_state(new_hand.NewNotification.waiting_date)
        msg = await callback.message.edit_text(
            f"✏️ Текущая дата: {data["date"].strftime('%d.%m.%Y')} \n\n Выберите дату",
            reply_markup=await SimpleCalendar(locale="C").start_calendar(),
        )
    elif data["repeat_type"] == "timer":
        await state.set_state(new_hand.NewNotification.waiting_timer)
        msg = await callback.message.edit_text(
            f"✏️ Текущее время напоминания: {data["timer_str"]} \n\n Через сколько времени напомнить?",
            reply_markup=service.merge_keyboards(
                new_kb.get_timer_keyboard(new_hand.TimerCallback),
                edit.get_back_keyboard(),
            ),
        )
    elif data["repeat_type"] == "week":
        await state.set_state(new_hand.NewNotification.waiting_weekdays)
        msg = await callback.message.edit_text(
            f'✏️ Текущие дни недели: {new_hand.get_string_weekdays(data["weekdays"])} \n\n Выберите дни недели',
            reply_markup=new_kb.get_weekdays_keyboard(
                new_hand.WeekdaysCallback, data["week_days"], True
            ),
        )
    elif data["repeat_type"] == "month":
        await state.set_state(new_hand.NewNotification.waiting_month_day)
        msg = await callback.message.edit_text(
            f"✏️ Текущий день месяца: {data["month_day"] if data["month_day"].isdigit() else "последний день месяца"} \n\n Выберите в какой день месяца напоминать?",
            reply_markup=service.merge_keyboards(
                new_kb.get_month_day_keyboard(new_hand.MonthDayCallback),
                edit.get_back_keyboard(),
            ),
        )
    elif data["repeat_type"] == "year":
        await state.set_state(new_hand.NewNotification.waiting_year_month)
        msg = await callback.message.edit_text(
            f"✏️ Текущая дата: {data["year_month"]} \n\n Выберите в какой день и месяц напоминать?",
            reply_markup=service.merge_keyboards(
                new_kb.get_year_month_keyboard(
                    new_hand.YearMonthCallback,
                    1,
                    new_hand.months_names[1],
                    new_hand.months_days[1],
                ),
                edit.get_back_keyboard(),
            ),
        )
    await state.update_data(bot_msg=msg.message_id)


# ========================== Back Logic ==========================
@router.callback_query(EditNotification.waiting_edit_field, F.data == "editBack")
async def edit_back_to_confirmation_process(callback: CallbackQuery, state: FSMContext):
    await state.set_state(new_hand.NewNotification.waiting_confirm)
    await new_hand.confirmation_step(callback, state)


@router.callback_query(StateFilter("*"), F.data == "editBack")
async def edit_back_to_fields_process(callback: CallbackQuery, state: FSMContext):
    await edit_processing(callback, state)


# ========================== Message Delete Logic ==========================
@router.message(StateFilter(EditNotification))
async def delete_messages(message: Message):
    try:
        await message.delete()
    except Exception:
        pass
