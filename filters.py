from typing import Any
from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from vars import vars


class AdminFilter(BaseFilter):

    def __init__(self) -> None:
        super().__init__()

    async def __call__(self, message: Message) -> Any:
        return message.from_user.id in vars.database.get_admins()
    

class AdminStates(StatesGroup):

    add_promocodes = State()

    add_chat_admin_id = State()
    add_chat_admin_username = State()
    del_chat_admin = State()

    add_chat_id = State()
    add_chat_loc = State()

    add_loc_name = State()
    add_loc_lvl_up = State()
    add_loc_status_up = State()
    add_loc_leaderboard = State()
