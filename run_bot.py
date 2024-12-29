"""
This script initializes and runs a Telegram bot using the aiogram library.

Modules:
    asyncio: Provides support for asynchronous programming.
    logging: Provides a way to configure logging.
    aiogram: Telegram bot framework.
    decouple: Allows to read configuration from environment variables or .env file.
    redis.asyncio.client: Redis client for asynchronous operations.

Functions:
    _main(): Initializes the database and starts the bot polling.

Variables:
    API_TOKEN (str): The API token for the Telegram bot, read from environment variables.
    redis_client (Redis): Redis client instance for storing bot state.
    bot (Bot): Instance of the Telegram bot.
    storage (RedisStorage): Redis storage for finite state machine (FSM) data.
    dp (Dispatcher): Dispatcher for handling updates and routing them to handlers.

Routers:
    start_router: Router for handling start commands.
    registration_router: Router for handling registration commands.
    basic_router: Router for handling basic commands.

Usage:
    Run this script to start the Telegram bot.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from decouple import config
from redis.asyncio.client import Redis

from database.database_manager import init_db
from handlers.basic_handlers.default_handler import default_router
from handlers.basic_handlers.start_handler import start_router
from handlers.registration_handler.registration_handlers import registration_router
from handlers.tasks_handlers.add_task_handler import add_task_router
from handlers.tasks_handlers.list_tasks_handler import list_tasks_router
from handlers.tasks_handlers.search_task_handler import search_tasks_router

logging.basicConfig(level=logging.INFO)

API_TOKEN: str = config("API_TOKEN")  # type: ignore


redis_client: Redis = Redis(
    host=config("REDIS_HOST"),  # type: ignore
    port=config("REDIS_PORT"),
    db=0,
    decode_responses=True,
)


bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = RedisStorage(redis=redis_client)
dp = Dispatcher(bot=bot, storage=storage)

dp.include_router(router=start_router)
dp.include_router(router=registration_router)
dp.include_router(router=add_task_router)
dp.include_router(router=list_tasks_router)
dp.include_router(router=search_tasks_router)
dp.include_router(router=default_router)


async def _reset_all_states() -> None:
    keys = await redis_client.keys("fsm:*")
    if keys:
        await redis_client.delete(*keys)

async def fetch_all_from_redis() -> dict:
    # Создаем подключение к Redis

    # Получаем все ключи в базе данных Redis
    keys = await redis_client.keys('*')

    # Словарь для хранения всех значений
    data = {}

    # Получаем значения для каждого ключа
    for key in keys:
        value = await redis_client.get(key)
        # Пытаемся декодировать значение, если оно в байтовом формате
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        data[key] = value

    # Закрываем подключение
    await redis_client.close()
    print(data)
    return data

async def _main() -> None:
    await fetch_all_from_redis()
    # await _reset_all_states()
    # await init_db()
    # await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(_main())
