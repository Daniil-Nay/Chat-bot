from aiogram.filters import Command
from aiogram.types import Message
from aiogram.dispatcher.router import Router

from database import create_table, DB_upload_data, DB_get_data
from lexicon_data import handlers_text

# from database import DB_upload_data


r: Router = Router()

@r.message(Command("start"))
async def cmd_start(message: Message):
    await create_table(message.from_user.username,message.from_user.id)
    await DB_upload_data("users_info", 'language_code', message.from_user.id, message.from_user.language_code)
    await message.answer(text = await handlers_text(message.from_user.language_code,'start'),parse_mode="html")



@r.message(Command("help"))
async def cmd_start(message: Message):
    print(message.from_user.language_code)
    is_admin = await DB_get_data("users_info","is_admin",message.from_user.id)
    text = 'help_admin' if is_admin else 'help'
    await message.answer(text = await handlers_text(message.from_user.language_code,text),parse_mode="html")
