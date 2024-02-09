from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message,CallbackQuery
from aiogram.dispatcher.router import Router
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import DB_upload_data, DB_get_data
from lexicon_data import handlers_text
# from database import DB_upload_data


r: Router = Router()
class UserSettingsStates(StatesGroup):
    typing_age = State()

start_keyboard = None
@r.message(Command('settings'))
async def user_settings(message: Message)->None:
    global start_keyboard
    is_activated = await DB_get_data("users_info","is_mode_on",message.from_user.id)
    print("is_activated", type(is_activated),is_activated)
    buttons = [[
        types.InlineKeyboardButton(
            text=await handlers_text(message.from_user.language_code,'gender'),
            callback_data = "Choose gender"
        )],
        [types.InlineKeyboardButton(
            text=await handlers_text(message.from_user.language_code, 'age'),
            callback_data="Choose age"
        )],
        [types.InlineKeyboardButton(
            text=await handlers_text(message.from_user.language_code, 'is_hidden'),
            callback_data=("hide_anything_off" if is_activated==0 else "hide_anything_on")
        )]
    ]
    start_keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        await handlers_text(message.from_user.language_code, 'text settings'),
        reply_markup=start_keyboard,
        parse_mode='html'
    )


@r.callback_query(F.data=="back_button")
async def back_request(callback:CallbackQuery):
    await callback.message.edit_text(
        await handlers_text(callback.from_user.language_code, 'text settings'),
        reply_markup=start_keyboard,
        parse_mode='html'
    )

@r.callback_query(F.data=="Choose gender")
async def choose_gender(callback: CallbackQuery):
    buttons = [
        [types.InlineKeyboardButton(
            text=await handlers_text(callback.from_user.language_code, 'gender1'),
            callback_data="male"
        )],
        [types.InlineKeyboardButton(
            text=await handlers_text(callback.from_user.language_code, 'gender2'),
            callback_data="female"
        )],
        [types.InlineKeyboardButton(
            text=await handlers_text(callback.from_user.language_code, 'back'),
            callback_data="back_button"
        )]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(
        await handlers_text(callback.from_user.language_code,'gender'),
        reply_markup = keyboard
    )

@r.callback_query((F.data == "female") | (F.data == "male"))
async def final(callback: CallbackQuery):
    await DB_upload_data("users_info", "gender", callback.from_user.id, callback.data)
    await callback.message.edit_text(
        await handlers_text(callback.from_user.language_code,'success'),
        parse_mode="html"
    )



@r.callback_query(F.data=="Choose age")
async def choose_age(callback: CallbackQuery, state: FSMContext):
    button = InlineKeyboardBuilder()
    button.add(types.InlineKeyboardButton(
            text=await handlers_text(callback.from_user.language_code, 'back'),
            callback_data="back_button"
        ))

    await callback.message.edit_text(
        await handlers_text(callback.from_user.language_code, 'choose age'),
        parse_mode="html",
        reply_markup = button.as_markup()
    )
    await state.set_state(UserSettingsStates.typing_age)

@r.message(UserSettingsStates.typing_age)
async def choose_age(message:Message,state:FSMContext):
    user_age = message.text
    button1 = types.InlineKeyboardButton(
        text=await handlers_text(message.from_user.language_code, 'back'),
        callback_data="back_button"
    )
    button2 = types.InlineKeyboardButton(
        text=await handlers_text(message.from_user.language_code, 'cancel'),
        callback_data="cancel"
    )
    new_keyboard2 = types.InlineKeyboardMarkup(inline_keyboard=[[button2]])
    new_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[button1]])
    if user_age.isdigit() and 0<=int(user_age)<=120:
        await DB_upload_data("users_info", "age", message.chat.id, user_age)
        await message.answer(
            await handlers_text(message.from_user.language_code,'success'),
            parse_mode='html',
            reply_markup = new_keyboard
        )
        await state.clear()
    else:
        await message.answer(
            await handlers_text(message.from_user.language_code, 'failure'),
            parse_mode='html',
            reply_markup = new_keyboard2
        )

@r.callback_query(F.data=="cancel")
async def cancel_button(callback:CallbackQuery,state:FSMContext):
    await callback.message.edit_text(
        await handlers_text(callback.from_user.language_code,'cancel'),
        parse_mode='html'
    )
    await state.clear()

@r.callback_query(F.data=="hide_anything_off")
async def hide_anything(callback:CallbackQuery):
    await DB_upload_data("users_info", "is_mode_on", callback.from_user.id, '0')
    buttons = [
        [types.InlineKeyboardButton(
            text=await handlers_text(callback.from_user.language_code, 'hide_anything_off'),
            callback_data="hide_anything_on"
        )],
        [types.InlineKeyboardButton(
            text=await handlers_text(callback.from_user.language_code, 'back'),
            callback_data="back_button"
        )]
    ]
    new_keyboard = types.InlineKeyboardMarkup(inline_keyboard = buttons)
    await callback.message.edit_text(
        await handlers_text(callback.from_user.language_code, 'hide_anything'),
        parse_mode="html",
        reply_markup=new_keyboard
    )

@r.callback_query(F.data=="hide_anything_on")
async def hide_anything(callback:CallbackQuery):
    await DB_upload_data("users_info",  "is_mode_on", callback.from_user.id, '1')
    buttons = [
        [types.InlineKeyboardButton(
            text=await handlers_text(callback.from_user.language_code, 'hide_anything_on'),
            callback_data="hide_anything_off"
        )],
        [types.InlineKeyboardButton(
            text=await handlers_text(callback.from_user.language_code, 'back'),
            callback_data="back_button"
        )]
    ]
    new_keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(
        await handlers_text(callback.from_user.language_code, 'hide_anything'),
        parse_mode="html",
        reply_markup=new_keyboard
    )