import asyncio
import json
import time

import priority as priority
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.methods import SendMessage
from database import DB_upload_data, DB_get_random_user, DB_get_data
from database.db import DB_upload_data_test
from lexicon_data import handlers_text

r: Router = Router()
flag:int = 0
f2 = 1
states = {
    "search_on":"1",
    "search_off":"0"
}
class States(StatesGroup):
    complaint_typing = State()
@r.message(Command("surf"))
async def StartSearchs(message: Message,bot:Bot):
    global flag,f2
    f2 = 1
    button = InlineKeyboardButton(
        text = await handlers_text(message.from_user.language_code,'cancel'),
        callback_data="cancel_button"
    )
    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
    srm = await message.answer(text=await handlers_text(message.from_user.language_code,"surf_mode"),
                         parse_mode="html",
                         reply_markup=new_keyboard
                         )
    await asyncio.sleep(2)
    await DB_upload_data("users_info",  "search_status", message.from_user.id, states["search_on"])
    max_search_time = 60  # Максимальное время поиска в секундах
    search_start_time = time.time()  # Запомнить время начала поиска
    print(message.from_user.id)
    is_mode_activated = (await DB_get_data("users_info","is_mode_on", message.from_user.id))
    if f2!=0:
        k = 0
        partner_id, partner_name,lng_code,mode = (await DB_get_random_user(message.from_user.id))
        print("PARTNER_NAME",partner_name)
        while time.time() - search_start_time < max_search_time and f2!=0:
            await asyncio.sleep(2)
            if partner_name is None:
                partner_id, partner_name,lng_code,mode = (await DB_get_random_user(message.from_user.id))
                print("партнер не был найден")
            elif partner_name is not None:
                await DB_upload_data("users_info",  'chat_partner', message.from_user.id, json.dumps((partner_id,lng_code,partner_name,mode)))
                await DB_upload_data("users_info",  'chat_partner', partner_id,json.dumps((message.from_user.id,message.from_user.language_code,message.from_user.first_name,is_mode_activated))
        )
                await DB_upload_data("users_info",'search_status', message.from_user.id, states["search_off"])
                await DB_upload_data("users_info",'search_status',   partner_id, states["search_off"])
                flag = 1
                f2 = 0
                k = 1
                break
        if f2==0:
            await srm.edit_text(
                    text=f"{await handlers_text(message.from_user.language_code, 'partner_is_found')}",
                    parse_mode="html"
            )
        else:
            await srm.edit_text(
                text=f"{await handlers_text(message.from_user.language_code, 'partner_is_not_found')}",
                parse_mode="html"
            )
    else:
         print("Поиск партнера завершен в {} секунд или прерван".format(max_search_time))

@r.callback_query(F.data=="cancel_button")
async def cancel_button(callback:CallbackQuery):
    global f2
    print("CALBACK ID",callback.from_user.id)
    await DB_upload_data("users_info", "search_status", callback.from_user.id, states["search_off"])
    await callback.message.edit_text(
        await handlers_text(callback.from_user.language_code,'search_cancel'),
        parse_mode='html'
    )
    f2 = 0

#07 02 24
partner_id = None
@r.message(Command("stop"))
async def StopDialogue(message:Message,bot:Bot):
    global flag
    global partner_id
    flag = 0
    button = InlineKeyboardButton(
        text = "отправить жалобу",
        # text=await handlers_text(message.from_user.language_code, 'complaint'),
        callback_data="complaint_button"
    )
    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
    partner_id,partner_lng_code,nickname, mode = json.loads((await DB_get_data("users_info","chat_partner",str(message.from_user.id))))
    print(f"current id {message.from_user.id}")
    print(f"partner data {partner_id}")
    print(type(partner_id))
    await DB_upload_data("users_info", 'chat_partner', int(partner_id),0)
    await DB_upload_data("users_info", 'chat_partner', message.from_user.id,0)
    print(f"код языка юзера {message.from_user.language_code}")
    # print(f"код языка юзера {partner_}")
    await message.answer(
        await handlers_text(message.from_user.language_code, 'dialogue_stopped'),
        parse_mode="html",
        reply_markup = new_keyboard
    )
    await bot.send_message(
        chat_id=partner_id,
        text=await handlers_text(partner_lng_code, 'dialogue_stopped'),
        parse_mode="html",
        reply_markup=new_keyboard
    )
@r.message(Command("share"))
async def ShareContact(message:Message,bot:Bot):
    if flag==1:
        res = json.loads((await DB_get_data("users_info","chat_partner",str(message.from_user.id))))
        await bot.send_message(
            chat_id = res[0],
            text = f"tag: @{message.from_user.username}\n"
        )

@r.callback_query(F.data=="complaint_button")
async def complaint_scenario(callback:CallbackQuery,state:FSMContext):
    await callback.message.edit_text("Введите сообщение для жалобы")
    await state.set_state(States.complaint_typing)


@r.message(States.complaint_typing)
async def complaint_typing(message:Message,state:FSMContext):
    print(message.text)
    print('partner_id',partner_id)
    #выводит ошибку об отсутстввии такой таблицы как complaints_list. Переделать функции с БД
    await DB_upload_data_test("complaints_list",["user_id","complaint_text","complaint_to_id"], message.from_user.id, (message.text, partner_id),"insert")
    # await DB_upload_data_test(message.from_user.id,"kek")
    await message.answer("жалоба написана!")
    await state.clear()

@r.message()
async def ChatEvent(message: Message,bot:Bot):
    if flag==1:
        res = (json.loads((await DB_get_data("users_info","chat_partner",message.from_user.id))))

        print(f" ДАННЫЕ В РЕС {res}")
        # await bot.send_message(
        #     chat_id = res[0],
        #     text = f"{message.from_user.first_name}:{message.text}"
        # )
        if res[3] and message.content_type!="text":
            await message.answer(
                text="у собеседника включен режим"
            )
        else:
            await message.copy_to(chat_id=int(res[0]))
    else:
        await message.answer(
            await handlers_text(message.from_user.language_code,'is_in_dialogue'),
            parse_mode="html"
        )



