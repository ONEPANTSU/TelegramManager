start_message = (
    "Здравствуйте, {0.first_name}! 🖐\n Я <b>Telegram Manager</b> "
    "для управелния активностью в телеграм-каналах!\n Что вам нужно?"
)
faq_message = (
    "<b>❓️ FAQ ❓️️️</b>\n"
    
    "\n➕ ДОБАВЛЕНИЕ АККАУНТА\n"
    " • <i>Необходимо отправить номер телефона.</i>\n"
    " • <i>Есть возможность авторизации при двухфакторной верификации.</i>\n"
    " • <i>Необходимо отправить код подтверждения.</i>\n"
    
    "\n🔒️ ПРИВАТНЫЙ КАНАЛ\n"
    " • <i>Приватный канал или приглосительная ссылка.</i>\n"
    
    "\n👀 НАКРУТКА ПРОСМОТРОВ\n"
    " • <i>Необходимо отправлять только публичные ссылки.</i>\n"
    
    "\n💥 НАКРУТКА РЕАКЦИЙ\n"
    " • <i>Необходимо отправлять только публичные ссылки.</i>\n"
    
    "\n👥 ПАРСЕР\n"
    " • <i>Непонятная хрень.</i>\n"
)
main_menu_massage = "📌 Главное меню 📌"
activity_menu_massage = "🍌 Активность 🍌"
user_message = "Начинается добавление аккаунта"
parser_message = "Начинается parsing"
user_phone_message = "Введите номер телефона ☎️"
user_password_message = "Введите пароль"
user_sms_message = "Введите код"
chose_activity_message = "Что будем делать?"
channel_link_message = "Введите ссылку на канал"
channel_name_message = "Введите название канала"
number_of_accounts_message = "Введите количество аккаунтов"
delay_message = "Введите задержку"
subscribe_message = "Подписка на канал осуществлена"
unsubscribe_message = "Отписка от канала осуществлена"
id_post_message = "Введите id поста"
number_of_post_message = "Введите количество постов"
viewer_post_message = "Посты просмотрены"
number_of_button_message = "Введите номер кнопки"
reactions_message = "Нажатие кнопки произошло успешно"
user_ask_message = "Аккаунт с паролем?"
isdigit_message = "Жду от вас циферки"

MESSAGES = {
    "start": start_message,
    "main_menu": main_menu_massage,
    "activity_menu": activity_menu_massage,
    "user": user_message,
    "parser": parser_message,
    "user_phone": user_phone_message,
    "user_password": user_password_message,
    "user_sms": user_sms_message,
    "channel_link": channel_link_message,
    "channel_name": channel_name_message,
    "number_of_accounts": number_of_accounts_message,
    "delay": delay_message,
    "subscribe": subscribe_message,
    "unsubscribe": unsubscribe_message,
    "id_post": id_post_message,
    "number_of_post": number_of_post_message,
    "viewer_post": viewer_post_message,
    "number_of_button": number_of_button_message,
    "reactions": reactions_message,
    "chose_activity": chose_activity_message,
    "isdigit": isdigit_message,
    "user_ask": user_ask_message,
    "faq": faq_message,
}
