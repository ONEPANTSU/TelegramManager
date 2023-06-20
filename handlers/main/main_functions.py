from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from texts.buttons import BUTTONS
from useful.instruments import logger


@logger.catch
def get_main_keyboard():
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    activity = KeyboardButton(BUTTONS["activity"])
    users = KeyboardButton(BUTTONS["users"])
    task = KeyboardButton(BUTTONS["task"])
    count_users = KeyboardButton(BUTTONS["count_users"])

    markup.add(activity, task, users, count_users)
    return markup


@logger.catch
async def main_menu(message, message_text):
    await message.answer(
        text=message_text,
        reply_markup=get_main_keyboard(),
    )
