"""
This module contains the handler for the /start command and the "главное меню" text message.

The handler initiates the user registration process if the user is not already registered.
If the user is already registered, it provides a basic keyboard for further interaction.

Functions:
    cmd_start(message: types.Message, state: FSMContext): Handles the /start command and "главное меню" text message.
"""
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database.database_manager import get_user_by_id
from handlers.basic_handlers.basic_keyboard import give_basic_keyboard
from handlers.basic_handlers.basic_state import start_menu
from handlers.registration_handler.registration_states_group import RegistrationStates

start_router: Router = Router()


@start_router.message(F.text.casefold() == "главное меню")
@start_router.message(Command('start'))
async def cmd_start(message: types.Message, state: FSMContext):
    """
    Handles the /start command for initiating the user registration process.

    This asynchronous function checks if the user is already registered. If the user is not registered,
    it initiates the registration process by asking for the user's name. If the user is already registered,
    it informs the user and provides a basic keyboard for further interaction.

    Args:
        message (types.Message): The message object containing the command and user information.
        state (FSMContext): The finite state machine context for managing user states.

    Returns:
        None
    """
    if message.from_user is None:
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return
    
    already_registered_text = (
        "Добро пожаловать!"
        "Используйте кнопки ниже для управления задачами."
    )
    user_id = message.from_user.id
    await state.clear()
    if await get_user_by_id(user_id) is not None:
        await message.answer(
            already_registered_text,
            reply_markup=await give_basic_keyboard(),
        )
        await state.set_state(start_menu)
        return
    await state.set_state(RegistrationStates.awaiting_name)
    await message.answer(
        "Привет! Давайте начнем регистрацию. Пожалуйста, укажите ваше имя.",
        reply_markup=await give_basic_keyboard(),
    )
