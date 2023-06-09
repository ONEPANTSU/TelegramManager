from aiogram import Dispatcher
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

from handlers.activity.percent_timer import *
from states import ReactionsStates, SubscribeStates, UnsubscribeStates, ViewerPostStates
from texts.buttons import BUTTONS
from texts.messages import MESSAGES
from useful.callbacks import (
    reactions_callback,
    reactions_delay_callback,
    reactions_yes_no_confirm_callback,
    subscribe_callback,
    subscribe_delay_callback,
    subscribe_yes_no_confirm_callback,
    unsubscribe_all_callback,
    unsubscribe_callback,
    unsubscribe_delay_callback,
    unsubscribe_yes_no_confirm_callback,
    viewer_post_callback,
    viewer_post_delay_callback,
    viewer_yes_no_confirm_callback,
)
from useful.instruments import callback_dict, logger
from useful.keyboards import (
    ask_delay_keyboard,
    ask_delay_keyboard_reactions,
    ask_delay_keyboard_viewer,
    confirm_keyboard,
)


@logger.catch
async def chose_activity(message: Message):
    admin_list = get_admin()
    admin = message.from_user.username
    if admin in admin_list:
        await message.answer(
            text=MESSAGES["chose_activity"], reply_markup=activity_keyboard()
        )
    else:
        await message.answer(text=MESSAGES["access"], reply_markup=None)


"""
    SUBSCRIBE CHANNEL STATES⠀⠀⠀⠀⠀⠀⠀⠀
"""


@logger.catch
async def subscribe_query(query: CallbackQuery):
    await query.message.edit_text(text=MESSAGES["channel_link"], reply_markup=None)
    await SubscribeStates.channel_link.set()


@logger.catch
async def subscribe_channel_link_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        if answer.startswith("https://t.me/"):
            await state.update_data(channel_link=answer)
            accounts_len = await get_accounts_len(link=answer, sub=True)
            await message.answer(
                text=MESSAGES["number_of_accounts"].format(count=accounts_len)
            )
            await SubscribeStates.number_of_accounts.set()
        else:
            await message.answer(text=MESSAGES["link_error"])
            await SubscribeStates.channel_link.set()


@logger.catch
async def subscribe_number_of_accounts_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        accounts_len = await get_accounts_len()
        if not answer.isdigit():
            await message.answer(
                text=MESSAGES["isdigit"], reply_markup=ReplyKeyboardRemove()
            )
            await SubscribeStates.number_of_accounts.set()
        elif accounts_len < int(answer):
            await bot.send_message(
                chat_id=message.chat.id,
                text=MESSAGES["count_user_error"].format(count=accounts_len),
            )
            await SubscribeStates.number_of_accounts.set()
        else:
            await state.update_data(count=int(answer))
            data = await state.get_data()
            link = data["channel_link"]
            count = int(answer)
            await message.answer(
                text=MESSAGES["delay_ask"],
                reply_markup=ask_delay_keyboard(
                    message.from_user.id,
                    link,
                    count,
                    callback=subscribe_delay_callback,
                ),
            )
            await state.finish()


@logger.catch
async def subscribe_ask_delay_state(
    query: CallbackQuery, callback_data: dict, state: FSMContext
):
    if await not_command_checker(message=query.message, state=state):
        answer = callback_data["answer"]
        user_id = int(callback_data["user_id"])
        link, count = callback_dict[user_id]
        try:
            callback_dict.pop(user_id)
        except Exception as e:
            logger.error(
                f"Subscribe Ask Delay State Error (Callback {user_id} is not exist) {e}"
            )
        await state.update_data(channel_link=link)
        await state.update_data(count=count)
        await state.update_data(delay_ask=answer)
        if answer == BUTTONS["delay_1"]:  # Обычная задержка
            await query.message.edit_text(
                text=MESSAGES["delay_regular"], reply_markup=None
            )
            await SubscribeStates.delay.set()
        elif answer == BUTTONS["delay_2"]:  # Процентная задержка
            await query.message.edit_text(
                text=MESSAGES["delay_perсent"], reply_markup=None
            )
            await SubscribeStates.delay_percent.set()


@logger.catch
async def subscribe_delay_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        if not answer.isdigit():
            await message.answer(
                text=MESSAGES["isdigit"], reply_markup=ReplyKeyboardRemove()
            )
            await SubscribeStates.delay.set()
        else:
            await state.update_data(delay=int(answer))
            data = await state.get_data()
            user_id = message.from_user.id
            args = [data["channel_link"], data["count"], data["delay"]]
            callback_dict[user_id] = args
            await state.finish()
            await message.answer(
                text=MESSAGES["confirm"],
                reply_markup=confirm_keyboard(
                    user_id=user_id,
                    callback=subscribe_yes_no_confirm_callback,
                    is_percent=False,
                ),
            )


@logger.catch
async def subscribe_delay_percent_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        timing = get_timing(answer)
        if timing is None:
            await message.answer(
                text=MESSAGES["delay_perсent"], reply_markup=ReplyKeyboardRemove()
            )
            await SubscribeStates.delay_percent.set()
        else:
            data = await state.get_data()
            args = [data["channel_link"], data["count"]]
            user_id = message.from_user.id
            callback_dict[user_id] = [timing, args]
            await state.finish()
            await message.answer(
                text=MESSAGES["confirm"],
                reply_markup=confirm_keyboard(
                    user_id=user_id,
                    callback=subscribe_yes_no_confirm_callback,
                    is_percent=True,
                ),
            )


@logger.catch
async def subscribe_ask_confirm_query(query: CallbackQuery, callback_data: dict):
    user_id = int(callback_data["user_id"])
    is_percent = callback_data["is_percent"] == "True"
    answer = callback_data["answer"]
    if answer == BUTTONS["yes_confirm"]:  # Подтверждено
        if is_percent:
            timing, args = callback_dict[user_id]
            await subscribe_percent_confirm(args, timing, query.message)
        else:
            args = callback_dict[user_id]
            await subscribe_confirm(args, query.message)
        try:
            callback_dict.pop(user_id)
        except Exception as e:
            logger.error(
                f"Subscribe Ask Confirm Query Error (Callback {user_id} is not exist) {e}"
            )

    elif answer == BUTTONS["no_confirm"]:  # Не подтверждено
        await query.message.edit_text(text=MESSAGES["confirm_no"], reply_markup=None)
        try:
            callback_dict.pop(user_id)
        except Exception as e:
            logger.error(
                f"Subscribe Ask Confirm Query Error (Callback {user_id} is not exist) {e}"
            )


@logger.catch
async def subscribe_confirm(args, message):
    is_success = await subscribe_channel(args=args, prev_message=message)
    # if is_public:
    #     is_success = await subscribe_public_channel(args=args, prev_message=message)
    # else:
    #     is_success = await subscribe_private_channel(args=args, prev_message=message)
    if is_success:
        await message.answer(
            text=MESSAGES["subscribe"], reply_markup=get_main_keyboard()
        )
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text=MESSAGES["error"],
        )
        await message.answer(text=MESSAGES["channel_link"])
        await SubscribeStates.channel_link.set()


@logger.catch
async def subscribe_percent_confirm(args, timing, message):
    is_success, accounts = await percent_timer(
        timing,
        subscribe_channel,
        args,
        prev_message=message,
        return_accounts=True,
        is_sub=1,
    )

    if is_success:
        await message.answer(
            text=MESSAGES["subscribe"], reply_markup=get_main_keyboard()
        )

    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text=MESSAGES["error"],
        )
        await message.answer(text=MESSAGES["channel_link"])
        await SubscribeStates.channel_link.set()

    try:
        is_success = await unsubscribe_timing(accounts=accounts, channel_link=args[0])
        if is_success:
            await message.answer(
                text=MESSAGES["unsubscribe"], reply_markup=get_main_keyboard()
            )
    except Exception as e:
        logger.error(f"Subscribe Percent Confirm Error: {e}")


"""
    UNSUBSCRIBE CHANNEL STATES⠀⠀⠀⠀⠀⠀⠀⠀
"""


@logger.catch
async def unsubscribe_query(query: CallbackQuery):
    await query.message.edit_text(text=MESSAGES["channel_link"], reply_markup=None)
    await UnsubscribeStates.channel_link.set()


@logger.catch
async def unsubscribe_channel_link_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        if answer.startswith("https://t.me/"):
            await state.update_data(channel_link=answer)
            accounts_len = await get_accounts_len(link=answer, sub=False)
            await message.answer(
                text=MESSAGES["number_of_accounts"].format(count=accounts_len)
            )
            await UnsubscribeStates.number_of_accounts.set()
        else:
            await message.answer(text=MESSAGES["link_error"])
            await UnsubscribeStates.channel_link.set()


@logger.catch
async def unsubscribe_number_of_accounts_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        accounts_len = await get_accounts_len()
        if not answer.isdigit():
            await message.answer(
                text=MESSAGES["isdigit"], reply_markup=ReplyKeyboardRemove()
            )
            await UnsubscribeStates.number_of_accounts.set()
        elif accounts_len < int(answer):
            await bot.send_message(
                chat_id=message.chat.id,
                text=MESSAGES["count_user_error"].format(count=accounts_len),
            )
            await UnsubscribeStates.number_of_accounts.set()
        else:
            await state.update_data(count=int(answer))
            data = await state.get_data()
            link = data["channel_link"]
            count = int(answer)
            # is_public = data["is_public"]
            await message.answer(
                text=MESSAGES["delay_ask"],
                reply_markup=ask_delay_keyboard(
                    message.from_user.id,
                    link,
                    count,
                    callback=unsubscribe_delay_callback,
                ),
            )
            await state.finish()


@logger.catch
async def unsubscribe_ask_delay_state(
    query: CallbackQuery, callback_data: dict, state: FSMContext
):
    if await not_command_checker(message=query.message, state=state):
        answer = callback_data["answer"]
        user_id = int(callback_data["user_id"])
        link, count = callback_dict[user_id]
        try:
            callback_dict.pop(user_id)
        except Exception as e:
            logger.error(
                f"Unsubscribe Ask Delay State Error (Callback {user_id} is not exist): {e}"
            )
        await state.update_data(channel_link=link)
        await state.update_data(count=count)
        await state.update_data(delay_ask=answer)
        if answer == BUTTONS["delay_1"]:  # Обычная задержка
            await query.message.edit_text(
                text=MESSAGES["delay_regular"], reply_markup=None
            )
            await UnsubscribeStates.delay.set()
        elif answer == BUTTONS["delay_2"]:  # Процентная задержка
            await query.message.edit_text(
                text=MESSAGES["delay_perсent"], reply_markup=None
            )
            await UnsubscribeStates.delay_percent.set()


@logger.catch
async def unsubscribe_delay_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        if not answer.isdigit():
            await message.answer(
                text=MESSAGES["isdigit"], reply_markup=ReplyKeyboardRemove()
            )
            await UnsubscribeStates.delay.set()
        else:
            await state.update_data(delay=int(answer))
            data = await state.get_data()
            user_id = message.from_user.id
            args = [data["channel_link"], data["count"], data["delay"]]
            callback_dict[user_id] = args
            await state.finish()
            await message.answer(
                text=MESSAGES["confirm"],
                reply_markup=confirm_keyboard(
                    user_id=user_id,
                    callback=unsubscribe_yes_no_confirm_callback,
                    is_percent=False,
                ),
            )


@logger.catch
async def unsubscribe_delay_percent_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text

        timing = get_timing(answer)
        if timing is None:
            await message.answer(
                text=MESSAGES["delay_perсent"], reply_markup=ReplyKeyboardRemove()
            )
            await UnsubscribeStates.delay_percent.set()
        else:
            data = await state.get_data()
            args = [data["channel_link"], data["count"]]
            user_id = message.from_user.id
            callback_dict[user_id] = [timing, args]
            await state.finish()
            await message.answer(
                text=MESSAGES["confirm"],
                reply_markup=confirm_keyboard(
                    user_id=user_id,
                    callback=unsubscribe_yes_no_confirm_callback,
                    is_percent=True,
                ),
            )


@logger.catch
async def unsubscribe_ask_confirm_query(query: CallbackQuery, callback_data: dict):
    user_id = int(callback_data["user_id"])
    is_percent = callback_data["is_percent"] == "True"
    answer = callback_data["answer"]
    if answer == BUTTONS["yes_confirm"]:  # Подтверждено
        if is_percent:
            timing, args = callback_dict[user_id]
            await unsubscribe_percent_confirm(args, timing, query.message)
        else:
            args = callback_dict[user_id]
            await unsubscribe_confirm(args, query.message)
        try:
            callback_dict.pop(user_id)
        except Exception as e:
            logger.error(
                f"Unsubscribe Ask Confirm Query Error (Callback {user_id} is not exist): {e}"
            )
    elif answer == BUTTONS["no_confirm"]:  # Не подтверждено
        await query.message.edit_text(text=MESSAGES["confirm_no"], reply_markup=None)
        try:
            callback_dict.pop(user_id)
        except Exception as e:
            logger.error(
                f"Unsubscribe Ask Confirm Query Error (Callback {user_id} is not exist): {e}"
            )


@logger.catch
async def unsubscribe_confirm(args, message):
    is_success = await leave_channel(args=args, prev_message=message)
    # if is_public:
    #     is_success = await leave_public_channel(args=args, prev_message=message)
    # else:
    #     is_success = await leave_private_channel(args=args, prev_message=message)
    if is_success:
        await message.answer(
            text=MESSAGES["unsubscribe"], reply_markup=get_main_keyboard()
        )
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text=MESSAGES["error"],
        )
        await message.answer(text=MESSAGES["channel_link"])
        await UnsubscribeStates.channel_link.set()


@logger.catch
async def unsubscribe_percent_confirm(args, timing, message):
    is_success, accounts = await percent_timer(
        timing,
        leave_channel,
        args,
        prev_message=message,
        return_accounts=True,
        is_sub=-1,
    )
    if is_success:
        await message.answer(
            text=MESSAGES["unsubscribe"], reply_markup=get_main_keyboard()
        )

    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text=MESSAGES["error"],
        )
        await message.answer(text=MESSAGES["channel_link"])
        await UnsubscribeStates.channel_link.set()


"""
       POST VIEWERS STATES⠀⠀⠀⠀⠀⠀⠀⠀⠀
"""


@logger.catch
async def viewer_post_button(query: CallbackQuery):
    await query.message.edit_text(text=MESSAGES["channel_link"], reply_markup=None)
    await ViewerPostStates.id_channel.set()


@logger.catch
async def viewer_id_channel_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        if answer.startswith("https://t.me/"):
            await state.update_data(channel_link=answer)
            await message.answer(text=MESSAGES["id_post"])
            await ViewerPostStates.id_post.set()
        else:
            await message.answer(text=MESSAGES["link_error"])
            await ViewerPostStates.id_channel.set()


@logger.catch
async def viewer_id_post_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        if not answer.isdigit():
            await message.answer(
                text=MESSAGES["isdigit"], reply_markup=ReplyKeyboardRemove()
            )
            await ViewerPostStates.id_post.set()
        else:
            await state.update_data(last_post_id=int(answer))
            await message.answer(text=MESSAGES["number_of_post"])
            await ViewerPostStates.number_of_post.set()


@logger.catch
async def number_of_post_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        if not answer.isdigit():
            await message.answer(
                text=MESSAGES["isdigit"], reply_markup=ReplyKeyboardRemove()
            )
            await ViewerPostStates.number_of_post.set()
        else:
            await state.update_data(count_posts=int(answer))
            accounts_len = await get_accounts_len()
            await message.answer(
                text=MESSAGES["number_of_accounts"].format(count=accounts_len)
            )
            await ViewerPostStates.number_of_accounts.set()


@logger.catch
async def viewer_number_of_accounts_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        accounts_len = await get_accounts_len()
        if not answer.isdigit():
            await message.answer(
                text=MESSAGES["isdigit"], reply_markup=ReplyKeyboardRemove()
            )
            await ViewerPostStates.number_of_accounts.set()
        elif accounts_len < int(answer):
            await bot.send_message(
                chat_id=message.chat.id,
                text=MESSAGES["count_user_error"].format(count=accounts_len),
            )
            await ViewerPostStates.number_of_accounts.set()
        else:
            await state.update_data(count_accounts=int(answer))
            data = await state.get_data()
            channel_link = data["channel_link"]
            count = int(answer)
            last_post_id = data["last_post_id"]
            count_posts = data["count_posts"]
            await message.answer(
                text=MESSAGES["delay_ask"],
                reply_markup=ask_delay_keyboard_viewer(
                    message.from_user.id, channel_link, count, last_post_id, count_posts
                ),
            )
            await state.finish()


@logger.catch
async def viewer_ask_delay_state(
    query: CallbackQuery, callback_data: dict, state: FSMContext
):
    if await not_command_checker(message=query.message, state=state):
        answer = callback_data["answer"]
        user_id = int(callback_data["user_id"])
        link, count_accounts, last_post_id, count_posts = callback_dict[user_id]
        try:
            callback_dict.pop(user_id)
        except Exception as e:
            logger.error(
                f"Viewer Ask Delay State Error (Callback {user_id} is not exist): {e}"
            )
        await state.update_data(channel_link=link)
        await state.update_data(count_accounts=count_accounts)
        await state.update_data(count_posts=count_posts)
        await state.update_data(last_post_id=last_post_id)
        await state.update_data(delay_ask=answer)
        if answer == BUTTONS["delay_1"]:  # Обычная задержка
            await query.message.edit_text(
                text=MESSAGES["delay_regular"], reply_markup=None
            )
            await ViewerPostStates.delay.set()
        elif answer == BUTTONS["delay_2"]:  # Процентная задержка
            await query.message.edit_text(
                text=MESSAGES["delay_perсent"], reply_markup=None
            )
            # Встатить нужное
            await ViewerPostStates.delay_percent.set()


@logger.catch
async def viewer_delay_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        if not answer.isdigit():
            await message.answer(
                text=MESSAGES["isdigit"], reply_markup=ReplyKeyboardRemove()
            )
            await ViewerPostStates.delay.set()
        else:
            await state.update_data(delay=int(answer))
            data = await state.get_data()
            args = [
                data["channel_link"],
                data["count_accounts"],
                data["last_post_id"],
                data["count_posts"],
                data["delay"],
            ]
            user_id = message.from_user.id
            callback_dict[user_id] = args

            await state.finish()
            await message.answer(
                text=MESSAGES["confirm"],
                reply_markup=confirm_keyboard(
                    user_id=user_id,
                    callback=viewer_yes_no_confirm_callback,
                    is_percent=False,
                ),
            )


@logger.catch
async def viewer_delay_percent_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text

        timing = get_timing(answer)
        if timing is None:
            await message.answer(
                text=MESSAGES["delay_perсent"], reply_markup=ReplyKeyboardRemove()
            )
            await ViewerPostStates.delay_percent.set()
        else:
            data = await state.get_data()
            args = [
                data["channel_link"],
                data["count_accounts"],
                data["last_post_id"],
                data["count_posts"],
            ]
            user_id = message.from_user.id
            callback_dict[user_id] = [timing, args]
            await state.finish()
            await message.answer(
                text=MESSAGES["confirm"],
                reply_markup=confirm_keyboard(
                    user_id=user_id,
                    callback=viewer_yes_no_confirm_callback,
                    is_percent=True,
                ),
            )


@logger.catch
async def viewer_ask_confirm_query(query: CallbackQuery, callback_data: dict):
    user_id = int(callback_data["user_id"])
    is_percent = callback_data["is_percent"] == "True"
    answer = callback_data["answer"]
    if answer == BUTTONS["yes_confirm"]:  # Подтверждено
        if is_percent:
            timing, args = callback_dict[user_id]
            await viewer_percent_confirm(args, timing, query.message)
        else:
            args = callback_dict[user_id][0]
            await viewer_confirm(args, query.message)
        try:
            callback_dict.pop(user_id)
        except Exception as e:
            logger.error(
                f"Viewer Ask Confirm Query Error (Callback {user_id} is not exist): {e}"
            )
    elif answer == BUTTONS["no_confirm"]:  # Не подтверждено
        await query.message.edit_text(text=MESSAGES["confirm_no"], reply_markup=None)
        try:
            callback_dict.pop(user_id)
        except Exception as e:
            logger.error(
                f"Viewer Ask Confirm Query Error (Callback {user_id} is not exist): {e}"
            )


@logger.catch
async def viewer_confirm(args, message):
    is_success = await view_post(args=args, prev_message=message)
    if is_success:
        await message.answer(
            text=MESSAGES["viewer_post"], reply_markup=get_main_keyboard()
        )
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text=MESSAGES["error"],
        )
        await message.answer(text=MESSAGES["channel_link"])
        await ViewerPostStates.id_channel.set()


@logger.catch
async def viewer_percent_confirm(args, timing, message):
    is_success = await percent_timer(timing, view_post, args, prev_message=message)
    if is_success:
        await message.answer(
            text=MESSAGES["viewer_post"], reply_markup=get_main_keyboard()
        )

    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text=MESSAGES["error"],
        )
        await message.answer(text=MESSAGES["channel_link"])
        await SubscribeStates.channel_link.set()


"""
        REACTIONS STATES⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
"""


@logger.catch
async def reactions_query(query: CallbackQuery):
    await query.message.edit_text(text=MESSAGES["channel_link"], reply_markup=None)
    await ReactionsStates.id_channel.set()


@logger.catch
async def reactions_id_channel_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        if answer.startswith("https://t.me/"):
            await state.update_data(channel_link=answer)
            await message.answer(text=MESSAGES["id_post"])
            await ReactionsStates.id_post.set()
        else:
            await message.answer(text=MESSAGES["link_error"])
            await ReactionsStates.id_channel.set()


@logger.catch
async def reactions_id_post_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        if not answer.isdigit():
            await message.answer(
                text=MESSAGES["isdigit"], reply_markup=ReplyKeyboardRemove()
            )
            await ReactionsStates.id_post.set()
        else:
            await state.update_data(post_id=int(answer))
            await message.answer(text=MESSAGES["number_of_button"])
            await ReactionsStates.number_of_button.set()


@logger.catch
async def number_of_button_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        if not answer.isdigit():
            await message.answer(
                text=MESSAGES["isdigit"], reply_markup=ReplyKeyboardRemove()
            )
            await ReactionsStates.number_of_button.set()
        else:
            await state.update_data(position=int(answer))
            accounts_len = await get_accounts_len()
            await message.answer(
                text=MESSAGES["number_of_accounts"].format(count=accounts_len)
            )
            await ReactionsStates.number_of_accounts.set()


@logger.catch
async def reactions_number_of_accounts_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        accounts_len = await get_accounts_len()
        if not answer.isdigit():
            await message.answer(
                text=MESSAGES["isdigit"], reply_markup=ReplyKeyboardRemove()
            )
            await ReactionsStates.number_of_accounts.set()
        elif accounts_len < int(answer):
            await bot.send_message(
                chat_id=message.chat.id,
                text=MESSAGES["count_user_error"].format(count=accounts_len),
            )
            await ReactionsStates.number_of_accounts.set()
        else:
            await state.update_data(count=int(answer))
            data = await state.get_data()
            link = data["channel_link"]
            count = int(answer)
            post_id = data["post_id"]
            position = data["position"]
            await message.answer(
                text=MESSAGES["delay_ask"],
                reply_markup=ask_delay_keyboard_reactions(
                    message.from_user.id, link, count, post_id, position
                ),
            )
            await state.finish()


@logger.catch
async def reactions_ask_delay_state(
    query: CallbackQuery, callback_data: dict, state: FSMContext
):
    if await not_command_checker(message=query.message, state=state):
        answer = callback_data["answer"]
        user_id = int(callback_data["user_id"])
        link, count, post_id, position = callback_dict[user_id]
        try:
            callback_dict.pop(user_id)
        except Exception as e:
            logger.error(
                f"Reaction Ask Delay State Error (Callback {user_id} is not exist): {e}"
            )
        await state.update_data(channel_link=link)
        await state.update_data(count=count)
        await state.update_data(post_id=post_id)
        await state.update_data(position=position)
        await state.update_data(delay_ask=answer)
        if answer == BUTTONS["delay_1"]:  # Обычная задержка
            await query.message.edit_text(
                text=MESSAGES["delay_regular"], reply_markup=None
            )
            await ReactionsStates.delay.set()
        elif answer == BUTTONS["delay_2"]:  # Процентная задержка
            await query.message.edit_text(
                text=MESSAGES["delay_perсent"], reply_markup=None
            )
            # Вставить нужное
            await ReactionsStates.delay_percent.set()


@logger.catch
async def reactions_delay_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text
        if not answer.isdigit():
            await message.answer(
                text=MESSAGES["isdigit"], reply_markup=ReplyKeyboardRemove()
            )
            await ReactionsStates.delay.set()
        else:
            await state.update_data(delay=int(answer))
            data = await state.get_data()
            args = [
                data["channel_link"],
                data["count"],
                data["post_id"],
                data["position"],
                data["delay"],
            ]
            user_id = message.from_user.id
            callback_dict[user_id] = args
            await state.finish()
            await message.answer(
                text=MESSAGES["confirm"],
                reply_markup=confirm_keyboard(
                    user_id=user_id,
                    callback=reactions_yes_no_confirm_callback,
                    is_percent=False,
                ),
            )


@logger.catch
async def reactions_delay_percent_state(message: Message, state: FSMContext):
    if await not_command_checker(message=message, state=state):
        answer = message.text

        timing = get_timing(answer)
        if timing is None:
            await message.answer(
                text=MESSAGES["delay_perсent"], reply_markup=ReplyKeyboardRemove()
            )
            await ReactionsStates.delay_percent.set()
        else:
            data = await state.get_data()
            args = [
                data["channel_link"],
                data["count"],
                data["post_id"],
                data["position"],
            ]
            user_id = message.from_user.id
            callback_dict[user_id] = [timing, args]
            await state.finish()
            await message.answer(
                text=MESSAGES["confirm"],
                reply_markup=confirm_keyboard(
                    user_id=user_id,
                    callback=reactions_yes_no_confirm_callback,
                    is_percent=True,
                ),
            )


@logger.catch
async def reactions_ask_confirm_query(query: CallbackQuery, callback_data: dict):
    user_id = int(callback_data["user_id"])
    is_percent = callback_data["is_percent"] == "True"
    answer = callback_data["answer"]
    if answer == BUTTONS["yes_confirm"]:  # Подтверждено
        if is_percent:
            timing, args = callback_dict[user_id]
            await reactions_percent_confirm(args, timing, query.message)
        else:
            args = callback_dict[user_id][0]
            await reactions_confirm(args, query.message)
        try:
            callback_dict.pop(user_id)
        except Exception as e:
            logger.error(
                f"Reaction Ask Confirm Query Error (Callback {user_id} is not exist): {e}"
            )
    elif answer == BUTTONS["no_confirm"]:  # Не подтверждено
        await query.message.edit_text(text=MESSAGES["confirm_no"], reply_markup=None)
        try:
            callback_dict.pop(user_id)
        except Exception as e:
            logger.error(
                f"Reaction Ask Confirm Query Error (Callback {user_id} is not exist): {e}"
            )


@logger.catch
async def reactions_confirm(args, message):
    is_success = await click_on_button(args=args, prev_message=message)
    if is_success:
        await message.answer(
            text=MESSAGES["reactions"], reply_markup=get_main_keyboard()
        )
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text=MESSAGES["error"],
        )
        await message.answer(text=MESSAGES["channel_link"])
        await ReactionsStates.id_channel.set()


@logger.catch
async def reactions_percent_confirm(args, timing, message):
    is_success = await percent_timer(
        timing, click_on_button, args, prev_message=message
    )
    if is_success:
        await message.answer(
            text=MESSAGES["reactions"], reply_markup=get_main_keyboard()
        )
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text=MESSAGES["error"],
        )
        await message.answer(text=MESSAGES["channel_link"])
        await SubscribeStates.channel_link.set()


def register_activity_handlers(dp: Dispatcher):
    dp.register_message_handler(chose_activity, text=[BUTTONS["activity"]])
    dp.register_callback_query_handler(subscribe_query, subscribe_callback.filter())
    dp.register_callback_query_handler(unsubscribe_query, unsubscribe_callback.filter())
    dp.register_callback_query_handler(
        viewer_post_button, viewer_post_callback.filter()
    )
    dp.register_callback_query_handler(reactions_query, reactions_callback.filter())
    dp.register_callback_query_handler(
        chose_activity, unsubscribe_all_callback.filter()
    )

    dp.register_message_handler(
        subscribe_channel_link_state, state=SubscribeStates.channel_link
    )
    dp.register_message_handler(
        subscribe_number_of_accounts_state, state=SubscribeStates.number_of_accounts
    )
    dp.register_callback_query_handler(
        subscribe_ask_delay_state, subscribe_delay_callback.filter()
    )
    dp.register_message_handler(subscribe_delay_state, state=SubscribeStates.delay)
    dp.register_message_handler(
        subscribe_delay_percent_state, state=SubscribeStates.delay_percent
    )
    dp.register_callback_query_handler(
        subscribe_ask_confirm_query, subscribe_yes_no_confirm_callback.filter()
    )

    dp.register_message_handler(
        unsubscribe_channel_link_state, state=UnsubscribeStates.channel_link
    )
    dp.register_message_handler(
        unsubscribe_number_of_accounts_state, state=UnsubscribeStates.number_of_accounts
    )
    dp.register_callback_query_handler(
        unsubscribe_ask_delay_state, unsubscribe_delay_callback.filter()
    )
    dp.register_message_handler(unsubscribe_delay_state, state=UnsubscribeStates.delay)
    dp.register_message_handler(
        unsubscribe_delay_percent_state, state=UnsubscribeStates.delay_percent
    )
    dp.register_callback_query_handler(
        unsubscribe_ask_confirm_query, unsubscribe_yes_no_confirm_callback.filter()
    )

    dp.register_message_handler(
        viewer_id_channel_state, state=ViewerPostStates.id_channel
    )
    dp.register_message_handler(viewer_id_post_state, state=ViewerPostStates.id_post)
    dp.register_message_handler(
        number_of_post_state, state=ViewerPostStates.number_of_post
    )
    dp.register_message_handler(
        viewer_number_of_accounts_state, state=ViewerPostStates.number_of_accounts
    )
    dp.register_callback_query_handler(
        viewer_ask_delay_state, viewer_post_delay_callback.filter()
    )
    dp.register_message_handler(viewer_delay_state, state=ViewerPostStates.delay)
    dp.register_message_handler(
        viewer_delay_percent_state, state=ViewerPostStates.delay_percent
    )
    dp.register_callback_query_handler(
        viewer_ask_confirm_query, viewer_yes_no_confirm_callback.filter()
    )

    dp.register_message_handler(
        reactions_id_channel_state, state=ReactionsStates.id_channel
    )
    dp.register_message_handler(reactions_id_post_state, state=ReactionsStates.id_post)
    dp.register_message_handler(
        number_of_button_state, state=ReactionsStates.number_of_button
    )
    dp.register_message_handler(
        reactions_number_of_accounts_state, state=ReactionsStates.number_of_accounts
    )
    dp.register_callback_query_handler(
        reactions_ask_delay_state, reactions_delay_callback.filter()
    )
    dp.register_message_handler(reactions_delay_state, state=ReactionsStates.delay)
    dp.register_message_handler(
        reactions_delay_percent_state, state=ReactionsStates.delay_percent
    )
    dp.register_callback_query_handler(
        reactions_ask_confirm_query, reactions_yes_no_confirm_callback.filter()
    )
