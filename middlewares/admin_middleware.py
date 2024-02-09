import aiosqlite
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

from database import DB_get_data


class AdminMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str,Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str,Any]
    )->Any:
        try:
            is_admin = (await DB_get_data("users_info","is_admin",event.from_user.id))
            if is_admin:
                return await handler(event, data)
            else:
                await event.reply("Вы не являетесь администратором")
        except aiosqlite.OperationalError as e:
            print("error",e)