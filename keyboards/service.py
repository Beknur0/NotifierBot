from aiogram.types import InlineKeyboardMarkup


def merge_keyboards(
    *keyboards: InlineKeyboardMarkup | None, horizontal: bool = False
) -> InlineKeyboardMarkup:
    """
    Объединяет несколько инлайн-клавиатур.
    Если horizontal=True, объединяет их горизонтально (построчно).
    Игнорирует None и пустые клавиатуры.
    """
    # Фильтруем только те клавиатуры, которые реально переданы и не пустые
    valid_kbs = [kb.inline_keyboard for kb in keyboards if kb and kb.inline_keyboard]

    if not valid_kbs:
        return InlineKeyboardMarkup(inline_keyboard=[])

    if not horizontal:
        # Вертикальное объединение (как в вашем примере)
        rows = []
        for kb_rows in valid_kbs:
            rows.extend(kb_rows)
        return InlineKeyboardMarkup(inline_keyboard=rows)
    else:
        # Горизонтальное объединение (построчно)
        max_rows = max(len(kb_rows) for kb_rows in valid_kbs)
        rows = []

        for i in range(max_rows):
            current_row = []
            for kb_rows in valid_kbs:
                # Если у текущей клавиатуры есть эта строка, добавляем её кнопки
                if i < len(kb_rows):
                    current_row.extend(kb_rows[i])
            if current_row:
                rows.append(current_row)

        return InlineKeyboardMarkup(inline_keyboard=rows)


# # Использование:
# combined_keyboard = merge_keyboards(new.get_cancel_keyboard(), new.get_skip_description_keyboard())

# await message.answer("Текст сообщения", reply_markup=combined_keyboard)
