import asyncio
import time

import aiosqlite
from aiogram.types import Message

from database import DB_upload_data


async def notif_distribution(user_id:str,message:Message)->None:
    try:
        await message.copy_to(chat_id=user_id,
                              parse_mode="html")
    except aiosqlite.NotSupportedError as e:
        print(f"Oshibka",e)


async def ban_def(user_id: int, ban_duration: int) -> None:
    current_time = int(time.time())
    print(current_time)
    end_time = current_time + (ban_duration * 60)
    remaining_time = ban_duration * 60
    while current_time < end_time:
        # print(f"current time {current_time}, end_time {eend_time}")
        await DB_upload_data("users_info",  'blocked_until', user_id, remaining_time)
        await asyncio.sleep(10)
        current_time = int(time.time())

        remaining_time = end_time - current_time
        if remaining_time < 0:
            break
    await DB_upload_data("users_info",  'blocked_until',  user_id, 0)
