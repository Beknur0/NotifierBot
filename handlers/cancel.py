from aiogram import Router, F
from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from keyboards import start


router = Router()

@router.message(Command("cancel"))
async def process_cancel(message: Message, state: FSMContext, bot: Bot):
    current = await state.get_state()
    if current:
        data = await state.get_data()
        bot_msg = data.get("bot_msg")
        await state.clear()
        await message.answer(
            f"👋 Привет, {message.from_user.full_name}! \n Я твой личный помощник для напоминаний. \n\n Выберите действие:",
            reply_markup=start.get_start_keyboard(),
        )
        if bot_msg:
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=bot_msg)
            except Exception:
                pass

    try:
        await message.delete()
    except Exception:
        pass