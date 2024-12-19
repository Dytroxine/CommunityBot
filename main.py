from vars import vars
from aiogram import Dispatcher
from admin_handlers import admin_router, setup_evening_message_scheduler
from user_handlers import user_router, chat_router
from admin_handlers import setup_leaderboard_scheduler
import asyncio


async def main():
    try:
        dp = Dispatcher()
        dp.include_router(chat_router)
        dp.include_router(admin_router)
        dp.include_router(user_router)
        setup_leaderboard_scheduler(vars.bot)
        setup_evening_message_scheduler(vars.bot)
        await vars.bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(vars.bot)
    except Exception as e:
        print(f"Unexpected Error: {e}")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('goodbye!')
    except Exception as e:
        print(f"Unexpected Error: {e}")
