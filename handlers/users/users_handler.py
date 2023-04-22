from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.callback_data import CallbackData
from telethon import TelegramClient

from config import *
from handlers.activity.activity_handler import not_command_checker
from states import AddUserStates
from texts.buttons import BUTTONS
from texts.messages import MESSAGES
from useful.instruments import clients, code

yes_no_callback = CallbackData("yes_no", "answer", "phone")


async def add_user_button(message: Message):
    await message.answer(text=MESSAGES["user_phone"])
    await AddUserStates.phone.set()


async def phone_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        phone = message.text
        await state.update_data(phone=phone)
        await message.answer(text=MESSAGES["user_ask"], reply_markup=ask_keyboard(phone))
        await state.finish()


def ask_keyboard(phone):
    yes_button = InlineKeyboardButton(text=BUTTONS['yes'], callback_data=yes_no_callback.new(answer=BUTTONS['yes'], phone=phone))
    no_button = InlineKeyboardButton(text=BUTTONS['no'], callback_data=yes_no_callback.new(answer=BUTTONS['no'], phone=phone))
    act_keyboard = InlineKeyboardMarkup(row_width=2).add(yes_button, no_button)

    return act_keyboard


async def ask_state(query: CallbackQuery, callback_data: dict, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = callback_data["answer"]
        phone = callback_data["phone"]

        await state.update_data(phone=phone)
        await state.update_data(is_password=answer)
        if answer == BUTTONS['yes']:
            await query.message.edit_text(text=MESSAGES["user_password"], reply_markup=None)
            await AddUserStates.password.set()
        elif answer == BUTTONS['no']:
            await query.message.answer(text=MESSAGES["user_sms"])
            await connect(state=state, phone=phone)


async def password_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        password = message.text
        await state.update_data(password=password)
        phone = (await state.get_data())["phone"]
        await message.answer(text=MESSAGES["user_sms"])
        await connect(phone=phone, password=password, state=state)


async def connect(state, phone, password=None):
    client = TelegramClient(f"base/{phone}", API_ID, API_HASH)
    await client.connect()
    if password is not None:
        await client.start(phone=phone, password=password, state=state)
    else:
        await client.start(phone=phone, state=state)


async def sms_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        phone = (await state.get_data())["phone"]
        code[phone] = message.text
        is_password = (await state.get_data())["is_password"]
        if is_password == BUTTONS["yes"]:
            password = (await state.get_data())["password"]
            await clients[phone]._start(
                phone=phone, password=password, code_callback=code[phone]
            )
        else:
            await clients[phone]._start(
                phone=phone, code_callback=code[phone]
            )
        await state.finish()


def register_users_handlers(dp: Dispatcher):
    dp.register_message_handler(add_user_button, text=[BUTTONS["users"]])
    dp.register_message_handler(phone_state, state=AddUserStates.phone)
    dp.register_message_handler(password_state, state=AddUserStates.password)
    dp.register_message_handler(sms_state, state=AddUserStates.sms)
    dp.register_callback_query_handler(ask_state, yes_no_callback.filter())
