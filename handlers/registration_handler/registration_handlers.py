"""
This module contains handlers for the user registration process using the aiogram framework.

Handlers:
    handle_name: Handles the user's name input during the registration process.
    handle_phone: Handles the phone number input from the user during the registration process.
"""
import re

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from database.database_manager import add_user, get_user_by_id
from handlers.basic_handlers.basic_state import start_menu
from handlers.registration_handler.registration_states_group import RegistrationStates
from database.models import User

registration_router: Router = Router()


@registration_router.message(RegistrationStates.awaiting_name)
async def handle_name(message: types.Message, state: FSMContext):
    """
    Handles the user's name input during the registration process.

    This function is triggered when the user sends a message containing their name.
    It validates the input, stores the name temporarily, and prompts the user to enter their phone number.

    Args:
        message (types.Message): The message object containing the user's input.
        state (FSMContext): The finite state machine context for managing user states.
    """
    if message.from_user is None:
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return

    name = message.text

    if not name:
        await message.answer("Имя не может быть пустым. Пожалуйста, введите ваше имя.")
        return

    await state.update_data(name=name)
    await message.answer(f"Прекрасно, {name}! Теперь введите свой номер телефона.")
    await state.set_state(RegistrationStates.awaiting_phone)


@registration_router.message(RegistrationStates.awaiting_phone)
async def handle_phone(message: types.Message, state: FSMContext):
    """
    Handles the phone number input from the user during the registration process.

    Args:
        message (types.Message): The message object containing the user's input.
        state (FSMContext): The finite state machine context for the current user.
    """
    if message.from_user is None:
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return

    user_id = message.from_user.id
    phone = message.text

    if not phone:
        await message.answer("Номер телефона не может быть пустым. Пожалуйста, введите ваш номер телефона.")
        return

    if not await _is_valid_phone(phone):
        await message.answer(
            "Номер телефона введен некорректно. Пожалуйста, введите номер телефона в формате +71234567890.",
        )
        return

    await state.update_data(phone=phone)
    state_data = await state.get_data()
    user_name = state_data.get("username", "")

    await _complete_registration(user_id, user_name, phone, message, state)


async def _is_valid_phone(phone: str) -> bool:
    """Validates the phone number."""
    number_regex = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    return bool(re.match(number_regex, phone))


async def _complete_registration(user_id: int, user_name: str, phone: str, message: types.Message, state: FSMContext):
    """Completes the registration by storing user data and sending confirmation."""
    await add_user(user_id, user_name, phone)
    user_data = await get_user_by_id(user_id)
    await _clean_state(state)

    if user_data is None:
        await message.answer("Error: Failed to register user.")
        return

    user: User = user_data
    await message.answer(
        f"Registration Successful! Your entered details:\nName: {user.name}\nPhone: {user.phone}",
    )
    await state.set_state(start_menu)


async def _clean_state(state: FSMContext) -> None:
    """
    Clean the state by resetting specific data fields and setting a new state.

    This function updates the FSMContext state by clearing the 'name' and 'phone' fields
    and then sets the state to 'awaiting_name'.

    Args:
        state (FSMContext): The finite state machine context to be updated.

    Returns:
        None
    """
    await state.update_data(name="", phone="")
    await state.set_state(RegistrationStates.awaiting_name)
