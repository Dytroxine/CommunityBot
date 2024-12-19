import asyncio

from db import Database
from dotenv import load_dotenv, set_key
from aiogram import Bot
from localisation_machine import LocMachine
import os

if not os.path.isfile('config.env'):
    with open('config.env', 'w') as file:
        file.write('''bot_token=YOUR_BOT_TOKEN
bot_password=YOUR_BOT_PASS
''')


class VariableManager:

    def __init__(self) -> None:
        load_dotenv('config.env')
        self.chats = []
        self.db_path = 'database.db'
        self.bot_token = os.environ.get('bot_token')
        self.bot_password = os.environ.get('bot_password')
        print(f"Bot token: {self.bot_token}")
        self.bot = Bot(token=self.bot_token, parse_mode='html')
        self.database = Database(self.db_path)
        self.loc = LocMachine(self.database, self.bot)

    @staticmethod
    def change_environ_key(key, value):
        _value = value.__str__()
        set_key('config.env', key, _value)
        return value


vars = VariableManager()
