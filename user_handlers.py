from aiogram import F, Router, Bot, types
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import Message, CallbackQuery, FSInputFile, ChatJoinRequest, InlineKeyboardMarkup, \
    InlineKeyboardButton, ChatMemberUpdated, ChatPermissions
from aiogram.filters.command import Command
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from vars import vars
import markups
from logger_config import logger

chat_router = Router()
chat_router.message.filter(F.chat.type != 'private')

user_router = Router()
user_router.message.filter(F.chat.type == 'private')

last_message_from_id = {}

bot = Bot(token=vars.bot_token)
eng_chat = vars.chats[0]


@chat_router.chat_join_request()
async def handle_join_request(event: ChatJoinRequest):
    # Получаем информацию о пользователе, подавшем заявку
    user = event.from_user
    user_id = user.id
    chat_id = event.chat.id
    username = user.username if user.username else "друг"
    if chat_id == eng_chat:
        button_text = "I am human"
        welcome_text = f"Hello, {event.from_user.first_name}! This is the Community Bot. We are happy to see you!\nTo join, please go through the captcha and click the button in 5 minutes."
    else:
        button_text = "Я человек"
        welcome_text = f"Добро пожаловать, {event.from_user.first_name}! Это бот Комьюнити. Рады, что вы решили присоединиться к нам!\n Чтобы вступить в чат, пожалуйста, пройдите капчу и нажмите кнопку в течение 5 минут."

    try:
        welcome_message = await bot.send_message(
            chat_id=user_id,
            text=welcome_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=button_text, callback_data=f"confirm_{user_id}_{chat_id}")]
            ])
        )
        print(f"Сообщение отправлено пользователю {username} ({user_id})")

        # Автоматически одобряем заявку на вступление
        await bot.approve_chat_join_request(chat_id, user_id)
        await bot.restrict_chat_member(chat_id, user_id, permissions=types.ChatPermissions(can_send_messages=False))

        pending_users[(user_id, chat_id)] = {
            'message_id': welcome_message.message_id
        }

        # Schedule the user removal in 5 minutes if not verified
        scheduler = AsyncIOScheduler()
        scheduler.add_job(remove_unverified_user, "date", run_date=datetime.now() + timedelta(minutes=5),
                          args=[user_id, chat_id, bot])
        scheduler.start()
    except Exception as e:
        print(f"Не удалось отправить сообщение {username} ({user_id}): {e}")


pending_users = {}


@chat_router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
@logger.catch
async def on_user_leave(event: ChatMemberUpdated):
    user_id = event.old_chat_member.user.id
    chat_id = event.chat.id
    if user_id in pending_users:
        try:
            # Удаляем пользователя из pending_users
            del pending_users[(user_id, chat_id)]
            logger.info(f"User {user_id} left the chat {chat_id} and was removed from pending_users.")
        except Exception as e:
            logger.error(f"Error while handling user {user_id} leaving the chat {chat_id}: {e}")


async def remove_unverified_user(user_id, chat_id, bot: Bot):
    if (user_id, chat_id) in pending_users:
        try:
            # Remove user from the chat if not verified
            await bot.delete_message(
                chat_id=user_id,
                message_id=pending_users[(user_id, chat_id)]['message_id']
            )
            await bot.ban_chat_member(chat_id, user_id)
            await bot.unban_chat_member(chat_id, user_id)  # Unban to allow rejoining
            del pending_users[(user_id, chat_id)]
            logger.info(f"Removed unverified user {user_id} from chat {chat_id}")
        except Exception as e:
            logger.error(f"Error while trying to remove unverified user {user_id}: {e}")


@user_router.callback_query(F.data.startswith("confirm_"))
async def on_confirm_human(callback_query: CallbackQuery, bot: Bot):
    try:
        # Extract user_id and chat_id from callback_data
        _, user_id_str, chat_id_str = callback_query.data.split("_", 2)
        user_id = int(user_id_str)
        chat_id = int(chat_id_str)

        # Remove restriction from the user
        await bot.restrict_chat_member(chat_id, user_id, permissions=ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False
        ))

        # Remove user from pending_users list
        if (user_id, chat_id) in pending_users:
            # Delete the verification message
            await bot.delete_message(
                chat_id=user_id,
                message_id=pending_users[(user_id, chat_id)]['message_id']
            )
            del pending_users[(user_id, chat_id)]
        if chat_id == eng_chat:
            await callback_query.answer(text="Verification successful! You can now participate in the group.")
        else:
            await callback_query.answer(text="Верификация успешна! Вы можете писать в группу.")
        logger.info(f"User {user_id} verified successfully in chat {chat_id}")
    except Exception as e:
        logger.error(f"Error while confirming user {callback_query.from_user.id}: {e}")


@chat_router.message()
@logger.catch
async def chat_message(message: Message):
    print('chat message', message.chat)
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else message.from_user.first_name
    admins = vars.database.get_admins()
    chat_admins = vars.database.get_chat_admins_ids()
    if user_id in admins + chat_admins:
        return
    now = datetime.now()
    now_text = now.strftime('%d.%m.%Y %H:%M:%S')
    vars.database.add_user(
        user_id,
        username,
        now_text
    )
    vars.database.add_user_to_leaderboard(chat_id, user_id, username)

    global last_message_from_id
    if last_message_from_id.get(chat_id):
        if last_message_from_id[chat_id] == user_id:
            return
        else:
            last_message_from_id[chat_id] = user_id
    else:
        last_message_from_id.update({chat_id: user_id})

    print(last_message_from_id)
    last_message_date = vars.database.get_last_message_date(user_id)

    if last_message_date is not None and last_message_date != '':
        last_message_date = datetime.strptime(last_message_date, '%d.%m.%Y %H:%M:%S')
        if (now - last_message_date).seconds < 10:
            return

    # Проверка на наличие текста в сообщении
    if message.text and len(message.text) < 4:
        return

    if message.entities:
        for entity in message.entities:
            if entity.type == 'url':
                return

    msg_count = vars.database.update_message_count(user_id, now_text)
    vars.database.update_message_count_in_leaderboard(chat_id, user_id)
    if msg_count is None:
        return
    text = vars.loc.get_level_up_text(username, msg_count, chat_id)
    if text is not None:
        await message.answer(text=text)


@user_router.message(Command('start'))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    vars.database.add_user(
        user_id,
        username
    )
    text = vars.loc.get_start_text(message.from_user.id)
    await message.answer_photo(
        photo=FSInputFile("images/start_img.jpg"),
        caption=text,
        reply_markup=vars.loc.get_main_keyboard(message.from_user.id)
    )


@user_router.message(F.text.in_(markups.btn_current_level_eng.text))
async def current_level(message: Message):
    text = vars.loc.get_current_level_text(message.from_user.id, message.from_user.username)
    await message.answer(text=text)


@user_router.message(F.text.in_(markups.btn_my_rewards_eng.text))
async def my_rewards(message: Message):
    text, keyboard = vars.loc.get_rewards_text(message.from_user.id)
    await message.answer(text=text, reply_markup=keyboard)


@user_router.callback_query(F.data.startswith('gainRewards_'))
async def gain_rewards(callback: CallbackQuery):
    amount = int(callback.data.split('_')[1])
    messages = vars.loc.get_rewards(amount, callback.from_user.id)
    for message in messages:
        await callback.message.answer(message)
    await callback.answer(show_alert=False)


@user_router.message(Command('admin'))
async def connect_admin(message: Message):
    password = message.text.replace('/admin ', '')
    if password == vars.bot_password:
        vars.database.add_admin(message.from_user.id)
        await message.answer('Добро пожаловать', reply_markup=markups.keyboard_admin_main_menu)


@user_router.message()
async def trash_handler(message: Message):
    trash_text = vars.loc.get_trash_text(message.from_user.id)
    await message.answer(text=trash_text)
