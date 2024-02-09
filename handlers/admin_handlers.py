import asyncio
import json

from aiogram import Router, Bot, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from config import load_config
from database import DB_get_column_data, DB_upload_data, DB_get_data, DB_get_complaint, DB_upload_data_test
from database.db import DB_remove_complaint
from lexicon_data import handlers_text
from async_defs import notif_distribution, ban_def

r = Router()
# r.message.middleware.register(AdminMiddleware())
config = load_config()
db_path:str = config.db.database_path

class AdminStates(StatesGroup):
    notification_details = State()
    id_to_promote_proccess = State()
    id_to_demote_proccess = State()
    id_to_ban = State()
    ban_time = State()

@r.message(Command("notify"))
async def notify_users(message:Message,state:FSMContext)->None:
    await message.answer(
        text="write text to notify"
    )
    await state.set_state(AdminStates.notification_details)

@r.message(AdminStates.notification_details)
async def notification_sending_proccess(message:Message, state: FSMContext)->None:
    user_ids: list = await DB_get_column_data("users_info","user_id")
    tasks = [notif_distribution(user_id,message) for user_id in user_ids]
    await asyncio.gather(*tasks)
    await state.clear()

@r.message(Command("promote"))
async def promote_user(message: Message, state:FSMContext)->None:
    chat_ids = str(await DB_get_column_data("users_info","user_id"))
    try:
        await message.reply(
            text=f"{await handlers_text(message.from_user.language_code,'admin_promotion')}{chat_ids}",
            parse_mode="html"
        )
        await state.set_state(AdminStates.id_to_promote_proccess)
    except Exception as e:
        await message.reply(f"Ошибка, {e}")
        raise



@r.message(AdminStates.id_to_promote_proccess)
async def promotion_proccess(message:Message,bot: Bot, state:FSMContext)->None:
    chat_ids = await DB_get_column_data("users_info","user_id")
    if int(message.text) in chat_ids:
        await DB_upload_data("users_info", "is_admin", int(message.text), "1")

        await message.reply(
            text = f"Пользователь <b>{message.text}</b> повышен до админа",
            parse_mode="html"
        )

        await bot.send_message(
            chat_id=message.text,
            text="Вы повышены до админа!"
        )
    else:
        await message.reply(f"Ошибка, данного пользователя нет в списке")
        raise
    await state.clear()


@r.message(Command("demote"))
async def demote_user(message:Message, state:FSMContext)->None:
    chat_ids = str(await DB_get_column_data("users_info", "user_id"))
    try:
        await message.reply(
            text=f"{await handlers_text(message.from_user.language_code,'admin_demotion')}{chat_ids}",
            parse_mode="html"
        )

        await state.set_state(AdminStates.id_to_demote_proccess)
    except Exception as e:
        await message.reply(f"Ошибкd, {e}")
        raise

@r.message(AdminStates.id_to_demote_proccess)
async def demotion_proccess(message:Message,bot:Bot, state:FSMContext)->None:
    chat_ids = await DB_get_column_data("users_info","user_id")
    print("CHAT IDS", chat_ids)
    if int(message.text) in chat_ids:
        await DB_upload_data("users_info", "is_admin", int(message.text), "0")
        await message.reply(
            text = f"Пользователь <b>{message.text}</b> понижен",
            parse_mode="html")
        await bot.send_message(
            chat_id=message.text,
            text="Вы были сняты с должности админа"
        )
    else:
        await message.reply(f"Ошибка, данного пользователя нет в списке")
    await state.clear()


@r.message(Command("ban"))
async def ban_user(message:Message,state:FSMContext)->None:
    chat_ids: list = await DB_get_column_data("users_info","user_id")
    await message.reply(
        text=f"{await handlers_text(message.from_user.language_code, 'ban_text')}{chat_ids}",
        parse_mode="html"
    )
    await state.set_state(AdminStates.id_to_ban)

@r.message(AdminStates.id_to_ban)
async def ban_time(message: Message, state: FSMContext)->None:
    await message.reply("Введите время (в мин) для бана")
    await state.update_data(ctext=message.text)
    await state.set_state(AdminStates.ban_time)

@r.message(AdminStates.ban_time)
async def ban_proccess(message: Message, state: FSMContext)->None:
    data = await state.get_data()
    duration: int = int(message.text)
    await state.clear()
    await ban_def(data.get('ctext'),duration)

@r.message(Command("partner_data"))
async def DisplayInfo(message: Message)->None:
    # json.loads((await DB_get_data("users_info", "chat_partner", str(message.from_user.id))))
    partner_id = (json.loads((await DB_get_data("users_info","chat_partner",message.chat.id))))[0]
    data: dict = ((await DB_get_data("users_info","*",partner_id)))
    await message.answer(
       text=f"username: @{data[1]}\n"
            f"ID: {data[0]}\n"
            f"is_admin:{data[2]}\n"
            f"sex: {data[4]}\n"
              f"age: {data[5]}\n"
            f"language_code: {json.loads(data[9])[1]}\n",
        parse_mode="html"
    )

@r.message(Command("view_complaints"))
async def ComplaintsDetails(message:Message, bot: Bot)->None:
    complaint_details = await DB_get_complaint()
    print(complaint_details)
    if complaint_details!=None:
        buttons = [
            [types.InlineKeyboardButton(
                text="approv",
                callback_data="approv"
            )],
            [types.InlineKeyboardButton(
                text="disapprov",
                callback_data="disapprov"
            )]
            # [types.InlineKeyboardButton(
            #     text=await handlers_text(callback.from_user.language_code, 'back'),
            #     callback_data="back_button"
            # )]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(text=f"from ID:{complaint_details[0]}\n"
                                  f"to ID:{complaint_details[2]}\n"
                                  f"complaint_text:{complaint_details[1]}",
                             reply_markup = keyboard)
    else:
        await message.answer(text="none")
    # ПЕРЕДЕЛАТЬ ЛОГИКУ С БД, есть инфа типа @ КОТОРУЮ МОЖНО НЕ КМДАТЬ В БД
@r.callback_query((F.data == "approv") | (F.data == "disapprov"))
async def complaints_user_countings(callback:CallbackQuery)->None:
    complaint_details = await DB_get_complaint()
    get_complaints_count = (await DB_get_data("users_info","complaints_count",complaint_details[2]))
    if (F.data=="approv"):
        get_complaints_count += 1
        await DB_upload_data_test("users_info",["complaints_count"],complaint_details[2],(get_complaints_count,),"update")
        await DB_remove_complaint()
    else:
        await DB_remove_complaint()
        pass

    await callback.message.edit_text(
        text="success!"
    )
    if (get_complaints_count%5==0):
        print("hello")
        base_duration = 60  # Базовая длительность бана в минутах
        multiplier = 10  # Коэффициент, определяющий увеличение длительности бана за каждую жалобу
        ban_duration = base_duration + ((get_complaints_count + 1) * multiplier)  # Рассчитываем длительность бана
        await ban_def(complaint_details[2], ban_duration)


@r.message(Command("stats"))
async def statistics(message:Message,state:FSMContext)->None:
    pass