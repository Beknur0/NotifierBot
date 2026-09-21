from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import start

router = Router()


@router.message(Command(commands=["start"]))
async def start_function(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
    await state.clear()
    await message.answer(
        f"👋 Привет, {message.from_user.full_name}! \n Я твой личный помощник для напоминаний. \n\n Выберите действие:",
        reply_markup=start.get_start_keyboard(),
    )
    