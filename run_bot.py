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

from database_manager import init_db
from handlers.basic_handler import basic_router
from handlers.registration_handlers import registration_router
from handlers.start_handler import start_router

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
dp.include_router(router=basic_router)


async def _main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(_main())
