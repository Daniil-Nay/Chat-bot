
import asyncio
from aiogram import Bot
from aiogram import Dispatcher
from config import load_config
from database import DB_get_column_data
from handlers import user_handlers, settings_handlers, chat_handlers,admin_handlers
from middlewares.admin_middleware import AdminMiddleware
from middlewares.ban_middleware import BanMiddleware


# from middlewares import BanMiddleware, AdminMiddleware
#

async def main():
    config = load_config()
    bot: Bot = Bot(token=config.tg_bot.token)
    dp: Dispatcher = Dispatcher()
    #если отсутсвует таблица users_info, то banmiddleware начинает конфликтовать ИСПРАВИТЬ
    # #adminmiddleware конфликтует с столбцом "language_code" и ломает язык
    admin_handlers.r.message.middleware.register(AdminMiddleware())
    dp.message.middleware.register(BanMiddleware())
    dp.include_router(admin_handlers.r)
    dp.include_router(user_handlers.r)
    dp.include_router(settings_handlers.r)
    # dp.message.middleware.register(AdminMiddleware())
    dp.include_router(chat_handlers.r)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
