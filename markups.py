from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

btn_current_level_eng = KeyboardButton(text='Current level')
btn_current_level_ru = KeyboardButton(text='Текущий уровень')
btn_my_rewards_eng = KeyboardButton(text='My rewards')
btn_my_rewards_ru = KeyboardButton(text='Мои подарки')

btn_add_promocodes = KeyboardButton(text='Загрузить промокоды')
btn_list_of_promocodes = KeyboardButton(text='Список промокодов')
btn_leaderboard = KeyboardButton(text='Лидерборд')
btn_chat_admins = KeyboardButton(text='Чат админы')
btn_list_of_chat_admins = KeyboardButton(text='Список админов чатов')
btn_add_chat_admin = KeyboardButton(text='Добавить админа чата')
btn_del_chat_admin = KeyboardButton(text='Удалить админа чата')
btn_start_leaderboard = KeyboardButton(text='Запустить лидерборд')
btn_add_localisation = KeyboardButton(text='Добавить локализацию')
btn_list_of_localisations = KeyboardButton(text='Локализации')
btn_add_chat = KeyboardButton(text='Добавить чат')
btn_list_of_chats = KeyboardButton(text='Список чатов')
btn_main_menu = KeyboardButton(text='Главное меню')

keyboard_chat_admins = ReplyKeyboardMarkup(keyboard=[
    [btn_list_of_chat_admins],
    [btn_add_chat_admin, btn_del_chat_admin],
    [btn_main_menu]
], resize_keyboard=True)

keyboard_main_menu_btn = ReplyKeyboardMarkup(keyboard=[
    [btn_main_menu]
], resize_keyboard=True)

keyboard_admin_main_menu = ReplyKeyboardMarkup(keyboard=[
    [btn_add_promocodes, btn_list_of_promocodes],
    [btn_leaderboard, btn_start_leaderboard],
    [btn_chat_admins],
    [btn_list_of_chats, btn_add_chat],
    [btn_list_of_localisations],
    [btn_add_localisation]
], resize_keyboard=True)

lvl_up_text_eng = '''📈 Level up!

@{username} has reached level {level}!

After {lvl_left} levels, you will receive a status upgrade!
Keep chatting and send more messages to receive the reward 🎁'''

status_up_text_eng = '''⬆️Status upgrade!

@{username} has reached new status: {status}!
Congratulations! Go chat with the bot to receive a reward ✔️'''

leaderboard_text_eng = '''Top 3 users in the past week:
1. {username_1}
2. {username_2}
3. {username_3}'''

welcome_message_eng = '''🎁 The rewards are waiting for you!

We are glad that the our community is growing and more and more users are joining it! We’ve decided to make communication not only enjoyable and useful, but also profitable! 

For every 50 chat messages you send, you will receive a new level, and for every 5 levels you will receive a new status and reward!

• Level 5: Beginner (0.25 USD)

• Level 10: Enthusiast (0.5 USD)

• Level 15: User (0.75 USD)

• Level 20: Fan (1 USD)

• Level 25: Master (1.5 USD)

As soon as you earn a new achievement, the bot will notify you and you can get a reward by setting a command in this chat.

💬 Let's chat and make money together with Us!'''

all_rewards_completed_eng = '''✔️ All available rewards have been received!'''

trash_text_eng = '''✏ Unfortunately, I cannot execute this command. Please check out the available features of the bot below, and if you have a question, ask it in the Community chat.'''

user_status_eng = '''📃 Let's check your achievements!

@{username}
status: {status}
level: {level}

Join discussions, chat with other users and take it to the next level!'''

user_reward_eng = '''🔔 Congratulations on your new achievement!

Your promocode to receive the reward: {promocode}

📎 You can activate it in your personal account settings, in the Promo Code section!'''

no_promo_eng = '''Unfortunately there are no more {lvl} level promocodes! Wait and try again'''

receive_reward_eng = '''Receive rewards'''

choose_channel_text_eng = '''Choose channel'''

available_rewards_text_eng = '''Received rewards:

{received_rewards}

Available rewards:

{available_rewards}'''

no_received_rewards_text_eng = '''You don\'t have received rewards now!'''

no_rewards_text_eng = '''You don\'t have available rewards now!'''


def get_language_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Русский', callback_data='language_ru'),
         InlineKeyboardButton(text='English', callback_data='language_eng')]
    ])
    return keyboard


def get_choose_channel_keyboard(language='ru', callback_start='channelLevel'):
    if language == 'ru':
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Канал 1', callback_data=callback_start + '_ru'),
             InlineKeyboardButton(text='Канал 2', callback_data=callback_start + '_eng')]
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Channel 1', callback_data=callback_start + '_ru'),
             InlineKeyboardButton(text='Channel 2', callback_data=callback_start + '_eng')]
        ])
    return keyboard
