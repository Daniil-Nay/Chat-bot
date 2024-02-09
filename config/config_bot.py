from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv


@dataclass
class DatabaseConfig:
    database_path: str


@dataclass
class TgBot:
    token: str
    creator_id: int

@dataclass
class Config:
    tg_bot: TgBot
    db: DatabaseConfig


def load_config() -> Config:
    load_dotenv()
    return Config(tg_bot=TgBot(token=getenv("BOT_API_KEY"),
                               creator_id = int(getenv("CREATOR_ID"))),
                  db=DatabaseConfig(database_path=getenv("DATABASE_PATH")))


