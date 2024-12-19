import random

import gspread
from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import CellFormat, Color, format_cell_range, get_effective_format
from filters import AdminFilter, AdminStates
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pandas as pd
from vars import vars
import markups
import logging

active_chats = [vars.chats[0], vars.chats[1]]
logger = logging.getLogger(__name__)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

spreadsheet_id = YOUR_SPREADSHEET_ID
sheet = client.open_by_key(spreadsheet_id).sheet1

admin_router = Router()
admin_router.message.filter(AdminFilter(), F.chat.type == 'private')

red_format = CellFormat(
    backgroundColor=Color(1, 0, 0),
)


async def get_all_group_chats_from_updates(bot: Bot):
    updates = await bot.get_updates()
    group_chat_ids = set()
    for update in updates:
        if update.message and update.message.chat.type in ['group', 'supergroup']:
            group_chat_ids.add(update.message.chat.id)
    return list(group_chat_ids)


def get_random_message_from_sheet():
    try:
        messages = sheet.col_values(1)
        if messages:
            return random.choice(messages)
    except Exception as e:
        print(f"Ошибка при получении сообщения из Google Sheets: {e}")


def get_message_from_sheet(chat_id):
    try:
        if chat_id == vars.chats[1]:
            messages = sheet.col_values(2)

            while True:
                chosen_message_index = random.randint(1, len(messages))
                question = messages[chosen_message_index - 1]

                cell_format = get_effective_format(sheet, f"B{chosen_message_index}")
                if not cell_format or cell_format.backgroundColor != Color(1, 0, 0):
                    break

            format_cell_range(sheet, f"B{chosen_message_index}", red_format)

            template = f"◼️ Вопрос выходного дня ◼️\n\n{question}\n\nПодключайтесь к чату и делитесь своими мыслями на сегодняшнюю тему!"
            return template

        else:
            messages = sheet.col_values(1)

            while True:
                chosen_message_index = random.randint(1, len(messages))
                question = messages[chosen_message_index - 1]

                cell_format = get_effective_format(sheet, f"A{chosen_message_index}")
                if not cell_format or cell_format.backgroundColor != Color(1, 0, 0):
                    break

            format_cell_range(sheet, f"A{chosen_message_index}", red_format)

            template = f"◼️ Welcome to the Weekend Discussion ◼️\n\n{question}\n\nJoin the chat and share your thoughts on today's topic!"
            return template
    except Exception as e:
        print(f"Ошибка при получении сообщения из Google Sheets: {e}")


async def send_evening_message(bot: Bot):
    chat_ids = list(active_chats)

    for chat_id in chat_ids:
        try:
            message = get_message_from_sheet(chat_id)
            await bot.send_message(chat_id=chat_id, text=message)
            print(f"Вечернее сообщение отправлено в чат {chat_id}")
        except Exception as e:
            print(f"Не удалось отправить сообщение в чат {chat_id}: {e}")


def setup_evening_message_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_evening_message, CronTrigger(year=3000, month=1, day=1, hour=18, minute=0), args=[bot])
    scheduler.start()
    print("Планировщик вечерних сообщений запущен")


@admin_router.message(F.text.in_(markups.btn_main_menu.text))
@admin_router.message(Command('start'))
async def admin_start_cmd(message: Message, state: FSMContext):
    await message.answer('Выберите действие', reply_markup=markups.keyboard_admin_main_menu)
    await state.clear()


@admin_router.message(F.text.in_(markups.btn_list_of_promocodes.text))
async def list_of_promocodes(message: Message):
    promocodes = vars.database.get_promocodes()
    columns = ['Промокод', 'Уровень']
    df = pd.DataFrame(columns=columns)
    for promo in promocodes:
        df.loc[len(df)] = promo
    writer = pd.ExcelWriter('promos.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='sheet1', index=False)
    worksheet = writer.sheets['sheet1']
    worksheet.set_column(0, 0, 50)
    worksheet.set_column(1, 1, 10)
    writer.close()
    await message.answer_document(FSInputFile('./promos.xlsx', 'promos.xlsx'))


@admin_router.message(F.text.in_(markups.btn_add_promocodes.text))
async def add_promocodes(message: Message, state: FSMContext):
    await message.answer('Загрузите список промокодов', reply_markup=markups.keyboard_main_menu_btn)
    await state.set_state(AdminStates.add_promocodes)


@admin_router.message(AdminStates.add_promocodes, F.document)
async def add_parsed(message: Message, state: FSMContext, bot: Bot):
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    dest_path = 'promocodes.xlsx'
    await bot.download_file(file_path, dest_path)
    df = pd.read_excel(dest_path, header=None)
    _amount = 0
    for _, row in df.iterrows():
        promocode, level = row.loc[0:2]
        count = vars.database.add_promocode(promocode, level)
        _amount += count
    await message.answer(f'Добавлено {_amount} промокодов!', reply_markup=markups.keyboard_admin_main_menu)
    await state.clear()


@admin_router.message(F.text.in_(markups.btn_add_chat.text))
async def add_chat_start(message: Message, state: FSMContext):
    localisations = vars.database.get_localisations()
    if localisations == []:
        await message.answer('На данный момент локализаций нет!', reply_markup=markups.keyboard_admin_main_menu)
        return

    await message.answer('Введите айди чата', reply_markup=markups.keyboard_main_menu_btn)
    await state.set_state(AdminStates.add_chat_id)


@admin_router.message(AdminStates.add_chat_id)
async def add_chat_id(message: Message, state: FSMContext):
    await state.update_data(chat_id=message.text)

    localisations = vars.database.get_localisations()
    builder = InlineKeyboardBuilder()
    for localisation in localisations:
        builder.button(text=localisation[0], callback_data='chooseLoc_%s' % localisation[0])

    await message.answer('Выберите локализацию', reply_markup=builder.as_markup())
    await state.set_state(AdminStates.add_chat_loc)


@admin_router.callback_query(F.data.startswith('chooseLoc_'), AdminStates.add_chat_loc)
async def add_chat_loc(callback: CallbackQuery, state: FSMContext):
    chat_id = (await state.get_data())['chat_id']
    loc = callback.data.split('_')[1]
    vars.database.add_chat(chat_id, loc)
    await callback.message.answer('Чат добавлен', reply_markup=markups.keyboard_admin_main_menu)
    await state.clear()
    await callback.answer(show_alert=False)


@admin_router.message(F.text.in_(markups.btn_chat_admins.text))
async def chat_admins_menu(message: Message):
    await message.answer('Выберите действие', reply_markup=markups.keyboard_chat_admins)


@admin_router.message(F.text.in_(markups.btn_list_of_chat_admins.text))
async def list_of_chat_admins(message: Message):
    chat_admins = vars.database.get_chat_admins()
    text = 'Список админов:'
    for admin in chat_admins:
        text += f'\n{admin[0]} - @{admin[1]}'
    await message.answer(text)


@admin_router.message(F.text.in_(markups.btn_add_chat_admin.text))
async def add_chat_admin_start(message: Message, state: FSMContext):
    await message.answer('Введите ID чат-админа', reply_markup=markups.keyboard_main_menu_btn)
    await state.set_state(AdminStates.add_chat_admin_id)


@admin_router.message(AdminStates.add_chat_admin_id)
async def add_chat_admin_id(message: Message, state: FSMContext):
    user_id = message.text
    chat_admins = vars.database.get_chat_admins()
    if int(user_id) in chat_admins:
        await message.answer('Админ уже добавлен! Попробуйте снова')
        return
    await state.update_data(user_id=user_id)
    await message.answer('Введите имя для админа')
    await state.set_state(AdminStates.add_chat_admin_username)


@admin_router.message(AdminStates.add_chat_admin_username)
async def add_chat_admin_username(message: Message, state: FSMContext):
    username = message.text
    user_id = (await state.get_data())['user_id']
    vars.database.add_chat_admin(user_id=user_id, username=username)
    await message.answer('Чат-админ добавлен!', reply_markup=markups.keyboard_chat_admins)
    await state.clear()


@admin_router.message(F.text.in_(markups.btn_del_chat_admin.text))
async def del_chat_admin_start(message: Message, state: FSMContext):
    await message.answer('Введите ID чат-админа', reply_markup=markups.keyboard_main_menu_btn)
    await state.set_state(AdminStates.del_chat_admin)


@admin_router.message(AdminStates.del_chat_admin)
async def del_chat_admin(message: Message, state: FSMContext):
    user_id = message.text
    rowcount = vars.database.del_chat_admin(user_id=user_id)
    if rowcount == 0:
        await message.answer('Чат-админ не найден! Попробуйте снова')
        return
    await message.answer('Чат-админ удален', reply_markup=markups.keyboard_chat_admins)
    await state.clear()


@admin_router.message(F.text.in_(markups.btn_start_leaderboard.text))
async def start_leaderboard_chat(message: Message, bot: Bot):
    leaderboard = vars.database.get_leaderboard()
    chats = set([x[0] for x in leaderboard])
    builder = InlineKeyboardBuilder()
    for chat in chats:
        chat_name = (await bot.get_chat(chat)).full_name
        builder.button(text=chat_name, callback_data='startLeaderboard_%s' % chat)
    builder.adjust(2)
    await message.answer('Выберите канал, в котором хотите запустить лидерборд', reply_markup=builder.as_markup())


@admin_router.callback_query(F.data.startswith('startLeaderboard_'))
async def start_leaderboard(callback: CallbackQuery):
    print('start leaderboard')
    chat_id = int(callback.data.split('_')[1])
    await vars.loc.leaderboard(chat_id)
    await callback.message.answer('Лидерборд запущен')
    await callback.answer(show_alert=False)


@admin_router.message(F.text.in_(markups.btn_leaderboard.text))
async def leaderboard_table(message: Message):
    leaderboard = vars.database.get_leaderboard()
    columns = ['Chat ID', 'User ID', 'Username', 'Кол-во сообщений']
    df = pd.DataFrame(columns=columns)
    for user in leaderboard:
        user = list(user)
        user[0] = user[0].__str__()
        df.loc[len(df)] = user
    writer = pd.ExcelWriter('leaderboard.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='sheet1', index=False)
    worksheet = writer.sheets['sheet1']
    worksheet.set_column(0, 0, 20)
    worksheet.set_column(1, 1, 20)
    worksheet.set_column(2, 2, 20)
    worksheet.set_column(3, 3, 20)
    writer.close()
    await message.answer_document(FSInputFile('./leaderboard.xlsx', 'leaderboard.xlsx'))


async def send_leaderboard_automatically(bot: Bot):
    leaderboard = vars.database.get_leaderboard()
    chats = set([x[0] for x in leaderboard if x[0] in active_chats])

    for chat_id in chats:
        leaderboard_users = vars.database.get_leaderboard_by_chat(chat_id)

        if not leaderboard_users:
            continue

        # Формируем список топ-3 пользователей
        top_3 = sorted(leaderboard_users, key=lambda x: x[3], reverse=True)[:3]  # Сортировка по количеству сообщений
        if len(top_3) == 0:
            continue

        # Подготовка оформления сообщений
        if chat_id == vars.chats[0]:
            # Оформление сообщения на русском
            leaderboard_text = "🏆 Мы готовы объявить самых активных пользователей недели:\n\n"
        else:
            # Оформление сообщения на английском
            leaderboard_text = "🏆 We are ready to announce the most active users of the week:\n\n"

        medal_emojis = ["🥇", "🥈", "🥉"]

        for i, user in enumerate(top_3):
            user_id = user[1]  # Индекс 1 — это user_id
            username = user[2]  # Индекс 2 — это username (сохраненный в БД)

            try:
                # Получаем актуальный юзернейм пользователя
                user_info = await bot.get_chat_member(chat_id, user_id)
                actual_username = user_info.user.username if user_info.user.username else user_info.user.full_name

                # Проверяем, изменился ли юзернейм
                if actual_username != username:
                    # Обновляем юзернейм в базе данных
                    vars.database.update_username_in_leaderboard(user_id, chat_id, actual_username)

                # Используем актуальный юзернейм
                leaderboard_text += f"{medal_emojis[i]} @{actual_username}\n"

            except Exception as e:
                logger.error(f"Не удалось получить данные для пользователя {user_id}: {e}")
                leaderboard_text += f"{medal_emojis[i]} @{username}\n"

        if chat_id == -1002182322041:
            leaderboard_text += "\nПоздравляем! Кто попадет на лидерборд на следующей неделе?"
        else:
            leaderboard_text += "\nCongratulations! Who will get on the leaderboard next week?"

        try:
            await bot.send_message(chat_id=chat_id, text=leaderboard_text)
            logger.info(f"Leaderboard sent to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send leaderboard to chat {chat_id}: {e}")


def setup_leaderboard_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_leaderboard_automatically, CronTrigger(day_of_week='mon', hour=11, minute=0), args=[bot])
    scheduler.start()
    logger.info("Leaderboard scheduler started")


@admin_router.message(F.text.in_(markups.btn_list_of_chats.text))
async def list_of_chats(message: Message):
    chats = vars.database.get_chats()
    if chats == []:
        await message.answer('На данный момент чатов нет!', reply_markup=markups.keyboard_admin_main_menu)
        return
    for chat in chats:
        builder = InlineKeyboardBuilder()
        builder.button(text='Удалить', callback_data='deleteChat_%s' % chat[0])
        await message.answer('Чат ID: %s\nЛокализация: %s' % (chat[0], chat[1]), reply_markup=builder.as_markup())


@admin_router.callback_query(F.data.startswith('deleteChat_'))
async def delete_chat(callback: CallbackQuery):
    chat_id = callback.data.split('_')[1]
    vars.database.del_chat(chat_id)
    await list_of_chats(callback.message)
    await callback.answer(show_alert=False)


@admin_router.message(F.text.in_(markups.btn_add_localisation.text))
async def add_localisation_start(message: Message, state: FSMContext):
    await message.answer('Введите название для локализации', reply_markup=markups.keyboard_main_menu_btn)
    await state.set_state(AdminStates.add_loc_name)


@admin_router.message(AdminStates.add_loc_name)
async def add_localisation_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer('''Введите текст повышения уровня
Не забудьте добавить следующие тэги:
{username} - Тэг для юзернейма человека
{level} - Достигнутый уровень человеком
{lvl_left} - Оставшееся число уровней до след. статуса''', reply_markup=markups.keyboard_main_menu_btn)
    await state.set_state(AdminStates.add_loc_lvl_up)


@admin_router.message(AdminStates.add_loc_lvl_up)
async def add_localisation_lvl_up(message: Message, state: FSMContext):
    await state.update_data(lvl_up=message.text)
    await message.answer('''Введите текст повышения статуса
Не забудьте добавить следующие тэги:
{username} - Тэг для юзернейма человека
{status} - Достигнутый статус человеком''', reply_markup=markups.keyboard_main_menu_btn)
    await state.set_state(AdminStates.add_loc_status_up)


@admin_router.message(AdminStates.add_loc_status_up)
async def add_localisation_status_up(message: Message, state: FSMContext):
    await state.update_data(status_up=message.text)
    await message.answer('''Введите текст лидерборда
Не забудьте добавить следующие тэги:
{username_1}, {username_2}, {username_3} - Юзернеймы людей''', reply_markup=markups.keyboard_main_menu_btn)
    await state.set_state(AdminStates.add_loc_leaderboard)


@admin_router.message(AdminStates.add_loc_leaderboard)
async def add_localisation_leaderboard(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data['name']
    lvl_up = data['lvl_up']
    status_up = data['status_up']
    leaderboard = message.text
    vars.database.add_localisation(name, lvl_up, status_up, leaderboard)
    await message.answer('Локализация добавлена!', reply_markup=markups.keyboard_admin_main_menu)
    await state.clear()


@admin_router.message(F.text.in_(markups.btn_list_of_localisations.text))
async def list_of_localisations(message: Message):
    localisations = vars.database.get_localisations()
    if localisations == []:
        await message.answer('На данный момент локализаций нет!', reply_markup=markups.keyboard_admin_main_menu)
        return
    builder = InlineKeyboardBuilder()
    for localisation in localisations:
        builder.button(text=localisation[0], callback_data='deleteLoc_%s' % localisation[0])
    await message.answer('Список локализаций\nНажмите на кнопку для удаления', reply_markup=builder.as_markup())


@admin_router.callback_query(F.data.startswith('deleteLoc_'))
async def delete_localisation(callback: CallbackQuery):
    loc = callback.data.split('_')[1]
    vars.database.del_localisation(loc)

    localisations = vars.database.get_localisations()
    builder = InlineKeyboardBuilder()
    for localisation in localisations:
        builder.button(text=localisation[0], callback_data='deleteLoc_%s' % localisation[0])
    await callback.message.answer('Локализация удалена', reply_markup=builder.as_markup())
    await callback.answer(show_alert=False)
