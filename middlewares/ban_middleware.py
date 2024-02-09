import aiosqlite
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from database import DB_get_data, DB_upload_data, DB_upload_data_test, create_table
from aiogram.types import Message

from lexicon_data import handlers_text


class BanMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        try:
            db_data = (await DB_get_data("users_info","blocked_until",event.chat.id))
            print(f"ban_middleware data {db_data}")
            try:
                print(f"DB DATA BLOCKED UNTIL", db_data)
                if type(db_data)==int and db_data!=0:
                    await event.reply(f"Вы были забанены на {db_data/60} мин",parse_mode="html")
                else:
                    return await handler(event, data)
            except KeyError:
                print("oof keyerror damn")
                # await DB_upload_data( event.from_user.id, event.from_user.first_name)
        except aiosqlite.OperationalError as e:
            print("no such table", e)
            await create_table(event.from_user.username,event.from_user.id)
            await DB_upload_data("users_info", 'language_code', event.from_user.id, event.from_user.language_code)
            await event.answer(text=await handlers_text(event.from_user.language_code, 'start'),
                                         parse_mode="html")

            # await  DB_upload_data("Users_info","username",event.from_user.id,)
            # await DB_upload_data_test("users_info", ['language_code'], event.from_user.id, (event.from_user.language_code,), "insert")
