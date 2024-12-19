from aiogram import Bot
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from db import Database
import markups


class LocMachine:

    def __init__(self, database: Database, bot: Bot) -> None:

        self._bot = bot
        self._db = database
        self.statuses = {
            5: 'Beginner (0.25 USD)',
            10: 'Enthusiast (0.5 USD)',
            15: 'User (0.75 USD)',
            20: 'Fan (1 USD)',
            25: 'Master (1.5 USD)'
        }
        self._lvl_diff = 30
        self._status_diff = 5

    async def leaderboard(self, chat_id):
        leaderboard = self._db.get_leaderboard_by_chat(chat_id=chat_id)
        leaderboard = [user for user in leaderboard]
        if not leaderboard or len(leaderboard) < 3:
            return None
        trophy = "\U0001F3C6"
        first_place = "\U0001F947"
        second_place = "\U0001F948"
        third_place = "\U0001F949"

        text = f"{trophy} We are ready to announce the most active users of the week:\n\n"
        users = sorted(leaderboard, key=lambda x: x[3], reverse=True)

        if len(users) >= 1:
            text += f"{first_place} @{users[0][2]}\n"
        if len(users) >= 2:
            text += f"{second_place} @{users[1][2]}\n"
        if len(users) >= 3:
            text += f"{third_place} @{users[2][2]}\n"

        text += "\nCongratulations! Who will get on the leaderboard next week?"

        await self._bot.send_message(chat_id, text, parse_mode="HTML")

        self._db.clear_leaderboard_by_chat_id(chat_id=chat_id)

    def get_leaderboard_text(self, chat_id):
        leaderboard = self._db.get_leaderboard_by_chat(chat_id=chat_id)
        print(f"Leaderboard for chat {chat_id}: {leaderboard}")
        leaderboard = [user for user in leaderboard]
        if not leaderboard or len(leaderboard) < 3:
            print(f"Not enough data for leaderboard in chat {chat_id}")
            return None
        if chat_id == -1002182322041:
            trophy = "\U0001F3C6"
            first_place = "\U0001F947"
            second_place = "\U0001F948"
            third_place = "\U0001F949"
            text = f"{trophy} Мы готовы объявить самых активных пользователей недели:\n\n"
            users = sorted(leaderboard, key=lambda x: x[3], reverse=True)

            if len(users) >= 1:
                text += f"{first_place} @{users[0][2]}\n"
            if len(users) >= 2:
                text += f"{second_place} @{users[1][2]}\n"
            if len(users) >= 3:
                text += f"{third_place} @{users[2][2]}\n"

            text += "\nПоздравляем! Кто попадет на лидерборд на следующей неделе?"
        elif chat_id == -1002209105831:
            trophy = "\U0001F3C6"
            first_place = "\U0001F947"
            second_place = "\U0001F948"
            third_place = "\U0001F949"

            text = f"{trophy} We are ready to announce the most active users of the week:\n\n"
            users = sorted(leaderboard, key=lambda x: x[3], reverse=True)

            if len(users) >= 1:
                text += f"{first_place} @{users[0][2]}\n"
            if len(users) >= 2:
                text += f"{second_place} @{users[1][2]}\n"
            if len(users) >= 3:
                text += f"{third_place} @{users[2][2]}\n"

            text += "\nCongratulations! Who will get on the leaderboard next week?"
        return text

    def get_main_keyboard(self, user_id):

        language = self._db.get_user_language(user_id)
        builder = ReplyKeyboardBuilder()
        if language == 'eng':
            builder.add(markups.btn_current_level_eng, markups.btn_my_rewards_eng)
        else:
            builder.add(markups.btn_current_level_ru, markups.btn_my_rewards_ru)
        builder.adjust(1)
        return builder.as_markup(resize_keyboard=True)

    def get_level_up_text(self, username, msg_count, chat_id):

        if msg_count % self._lvl_diff != 0:
            return None
        localisation = self._db.get_localisation(chat_id)
        print('chat id is', chat_id, 'localisation is\n', localisation)
        if localisation is None:
            localisation = self._db.get_default_localisation()
        level = int(msg_count / self._lvl_diff)
        status = self.get_user_status(level)
        if level % self._status_diff == 0:
            text = localisation[1]
            kwargs = {'username': username, 'status': status}
        else:
            text = localisation[0]
            lvl_left = self._status_diff - (level % self._status_diff)
            kwargs = {'username': username, 'level': level, 'lvl_left': lvl_left}
        return text.format(**kwargs)

    def get_start_text(self, user_id):
        return markups.welcome_message_eng

    def get_current_level_text(self, user_id, username):

        msg_count = self._db.get_user_msg_count(user_id)
        level = int(msg_count / self._lvl_diff)
        status = self.get_user_status(level)
        kwargs = {
            'level': level,
            'status': status,
            'username': username
        }
        text = markups.user_status_eng
        return text.format(**kwargs)

    def get_user_status(self, level):

        for key in self.statuses.keys():
            if level < key:
                return self.statuses[key]

        return self.statuses[25]

    def get_trash_text(self, user_id):
        return markups.trash_text_eng

    def get_rewards_text(self, user_id):

        promos = self._db.get_user_promos(user_id)
        msg_count = promos[0]
        promos = promos[1:]
        status = int(msg_count / (self._status_diff * self._lvl_diff))
        available_promos = []
        received_promos = []

        promo_text = 'Promo for {lvl} level'
        received_promo_text = promo_text + ': {promo}'
        text = markups.available_rewards_text_eng
        false_text = markups.no_rewards_text_eng
        false_received_text = markups.no_received_rewards_text_eng
        btn_text = markups.receive_reward_eng

        for i in range(status):
            if not promos[i]:
                available_promos.append(promo_text.format(lvl=(i + 1) * 5))
            else:
                received_promos.append(received_promo_text.format(
                    lvl=((i + 1) * 5),
                    promo=promos[i]
                )
                )
        if len(available_promos) == 0:
            text = text.format(available_rewards=false_text, received_rewards='{received_rewards}')
        else:
            text = text.format(available_rewards='\n\n'.join(available_promos), received_rewards='{received_rewards}')
        if len(received_promos) == 0:
            text = text.format(received_rewards=false_received_text)
        else:
            text = text.format(received_rewards='\n\n'.join(received_promos))
        builder = InlineKeyboardBuilder()
        builder.button(text=btn_text, callback_data='gainRewards_%s' % len(available_promos))
        return text, builder.as_markup()

    def get_rewards(self, amount, user_id):

        promo_text = markups.user_reward_eng
        promos: list = self._db.get_user_promos(user_id)
        promos = list(promos[1:])
        messages = []
        for i in range(amount):
            _ind = promos.index(None)
            promos[_ind] = self._db.get_promocode((_ind + 1) * 5)
            if promos[_ind] is None:
                messages.append(markups.no_promo_eng.format(lvl=(i + 1) * 5))
            else:
                messages.append(promo_text.format(promocode=promos[_ind]))
        self._db.update_user_promos(user_id, promos)
        return messages
