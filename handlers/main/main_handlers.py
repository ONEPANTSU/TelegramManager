from aiogram import Dispatcher
from aiogram.types import Message

from handlers.main.main_functions import main_menu
from texts.buttons import BUTTONS
from texts.commands import COMMANDS
from texts.messages import MESSAGES


async def start_command(message: Message):
    await main_menu(message, message_text=MESSAGES["start"].format(message.from_user))


async def back_by_button(message: Message):
    await main_menu(message, message_text=MESSAGES["main_menu"])


async def back_by_command(message: Message):
    await main_menu(message, message_text=MESSAGES["main_menu"])


def register_main_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=[COMMANDS["start"]])
    dp.register_message_handler(back_by_button, text=[BUTTONS["back"]])
    dp.register_message_handler(back_by_command, commands=[COMMANDS["back"]])
