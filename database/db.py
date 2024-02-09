import json
from typing import Any

import aiosqlite
from config.config_bot import load_config
from aiocache import cached
from aiocache.serializers import PickleSerializer
config = load_config()
db_path: str = config.db.database_path


async def create_table(username: str, user_id: int):
    print(db_path)
    db = await aiosqlite.connect(db_path)
    mycursor = await db.cursor()
    await mycursor.execute("""CREATE TABLE IF NOT EXISTS users_info (
            user_id INTEGER PRIMARY KEY,
            name VARCHAR(50),
            is_admin BOOLEAN,
            blocked_until INTEGER,
            gender BOOLEAN,
            age INTEGER,
            is_mode_on BOOLEAN,
            complaints_count INTEGER
        )""")
    await db.commit()
    try:
        res = 1 if user_id == config.tg_bot.creator_id else 0
        await db.execute(f"INSERT INTO users_info(user_id,name,is_admin,blocked_until,gender,age,is_mode_on, complaints_count) "
                         f"VALUES (?,?,?,?,?,?,?,?)",
                         (user_id, username, res, 0,0,0,0,0))
        await db.commit()
        print("айди пользователя, айди чата и ник добавлены в бд!")
    except aiosqlite.IntegrityError as e:
        print("ошибка добавления пользователя в бд", e)
    finally:
        await mycursor.close()
        await db.close()

@cached(ttl=10, serializer=PickleSerializer())
async def DB_get_column_data(table_name:str,column_name:str):
    async with aiosqlite.connect(db_path) as connect:
        async with connect.execute(f"SELECT {column_name} from {table_name}") as cursor:
            column_data = [data[0] for data in (await cursor.fetchall())]
            print(f"column data",type(column_data))
        return column_data

@cached(ttl=10, serializer=PickleSerializer())
async def DB_get_data(table_name:str, column_name:str, user_id:int) -> dict:

    async with aiosqlite.connect(db_path) as connect:
        async with connect.execute(f"SELECT {column_name} FROM {table_name} WHERE user_id = ?", (user_id,)) as cursor:
            data = (await cursor.fetchone())
            print("Data in DB_get_data",data)
            try:
                if column_name!="*":
                    data = data[0]
            except Exception as e:
                print("exception",e)
    return data



@cached(ttl=10, serializer=PickleSerializer())
async def DB_upload_data(table_name: str, column_name: str, user: int, new_data: Any) -> None:
    # root = path.dirname(path.realpath(__file__))
    async with aiosqlite.connect(db_path) as connect:
        cursor = await connect.cursor()
        try:
            await cursor.execute(f"UPDATE {table_name} SET {column_name} = ? WHERE user_id = ?", (new_data, user))
            print(f"new data is {new_data}")
            await connect.commit()
        except aiosqlite.Error as e:
            print(f"Ошибка при выполнении запроса: {e}")
            await cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} TEXT")
            await connect.commit()
            # Повторите обновление после создания столбца
            await cursor.execute(f"UPDATE {table_name} SET {column_name} = ? WHERE user_id = ?", (new_data, user))
            await connect.commit()
        await cursor.close()

# async def DB_get_complaint():
#     async with aiosqlite.connect(db_path) as connection:
#         cursor = await connection.cursor()
#
#         # Выбираем одну жалобу для обработки (первую в очереди)
#         await cursor.execute("SELECT user_id, complaint_text, complaint_to_id FROM complaints_list ASC LIMIT 1")
#         complaint = await cursor.fetchone()
#         if complaint:
#             user_id, complaint_text, complaint_to_id = complaint
#             # await cursor.execute("DELETE FROM complaints_list WHERE user_id = ? AND complaint_text = ? AND complaint_to_id = ?", (user_id, complaint_text, complaint_to_id))
#
#             # Коммитим транзакцию
#             await connection.commit()
#             await cursor.close()
#             return complaint
#         else:
#             print("Нет жалоб для обработки.")
#             await cursor.close()
#             return None


async def DB_get_complaint():
    async with aiosqlite.connect(db_path) as connection:
        cursor = await connection.cursor()

        # Выбираем одну жалобу для обработки (первую в очереди)
        await cursor.execute("SELECT user_id, complaint_text, complaint_to_id FROM complaints_list ASC LIMIT 1")
        complaint = await cursor.fetchone()
        if complaint:
            # Коммитим транзакцию
            await connection.commit()
            await cursor.close()
            return complaint
        else:
            print("Нет жалоб для обработки.")
            await cursor.close()
            return None


async def DB_remove_complaint():
    async with aiosqlite.connect(db_path) as connection:
        cursor = await connection.cursor()
        await cursor.execute("SELECT user_id, complaint_text, complaint_to_id FROM complaints_list ASC LIMIT 1")
        user_id, complaint_text, complaint_to_id  = (await cursor.fetchone())
        print("ucc:",user_id,complaint_text,complaint_to_id)
        await cursor.execute("DELETE FROM complaints_list WHERE user_id = ? AND complaint_text = ? AND complaint_to_id = ?", (user_id, complaint_text, complaint_to_id))
        await connection.commit()

async def DB_upload_data_test(table_name: str, columns: list[str], user: int, values:tuple, type:str):
    async with aiosqlite.connect(db_path) as connection:
        cursor = await connection.cursor()
        print(f"values in db upload:{values}")
        await cursor.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} (
                   user_id INTEGER
               )""")
        # await cursor.execute(f"INSERT OR IGNORE INTO {table_name} (user_id) VALUES (?)", (user,))
        try:
            # Проверяем существование столбцов в таблице
            await cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = [column[1] for column in await cursor.fetchall()]

            # Добавляем новые столбцы, если их ещё нет в таблице
            new_columns = [column for column in columns if column not in existing_columns]
            for new_column in new_columns:
                print(f"NEW COLUMN: {new_column}")
                await cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {new_column} TEXT")

            # Вставляем данные в таблицу
            if type=="insert":
                set_columns = ", ".join([column for column in columns])
                print(f"columns in insert",set_columns)
                question_marks = ', '.join(['?' for _ in values])
                await cursor.execute(f"INSERT INTO {table_name} ({set_columns}) VALUES (?,{question_marks})",
                                     (user, *values))
            if type=="update":
                await cursor.execute(f"INSERT OR IGNORE INTO {table_name} (user_id) VALUES (?)", (user,))
                set_columns = ", ".join([f"{column} = ?" for column in columns])
                await cursor.execute(f"UPDATE {table_name} SET {set_columns} WHERE user_id = ?", (*values, user))
            # Коммитим транзакцию
            await connection.commit()

            print("Данные успешно внесены в таблицу.")
        except aiosqlite.Error as e:
            print(f"Ошибка при внесении данных: {e}")
        finally:
            await cursor.close()

# async def DB_upload_data_test(user_id: int, complaint_text: str):
#     async with aiosqlite.connect(db_path) as connection:
#         cursor = await connection.cursor()
#         await cursor.execute("""CREATE TABLE IF NOT EXISTS complaints_list (
#             user_id INTEGER,
#             complaint_text TEXT,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )""")
#         f = ""
#         print(f"insert {f}k")
#         # Вставляем данные в т
#         # аблицу
#         await cursor.execute("INSERT INTO complaints_list (user_id, complaint_text) VALUES (?, ?)", (user_id, complaint_text))
#
#         # Коммитим транзакцию
#         await connection.commit()
#
#         print("Жалоба успешно добавлена.")
#         await cursor.close()

@cached(ttl=10, serializer=PickleSerializer())
async def DB_get_random_user(execute_id:int):
    try:
            async with aiosqlite.connect(db_path) as connect:
                async with connect.cursor() as cursor:
                    try:
                        await cursor.execute("SELECT user_id, name, language_code, is_mode_on FROM users_info "
                                             "WHERE search_status = 1 AND user_id != ?  ORDER BY RANDOM() LIMIT 1",(execute_id,))
                        res = (await cursor.fetchall())[0]
                        # user_id,name = zip(*(await cursor.fetchall()))
                    except Exception as e:
                        res = (None,None,None,None)
                    print("res", res)
                    return res
    except Exception as e:
        print("Ошибка открытия БД",e)

