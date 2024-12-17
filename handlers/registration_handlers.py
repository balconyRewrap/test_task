# TODO: ADD DOCSTRING
import re

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from database_manager import add_user, get_user_by_id
from handlers.states_groups import RegistrationStates
from models import User
from temp_database_manager import TempDatabaseManager

registration_router: Router = Router()


async def _complete_registration(user_id: int, user_name: str, phone: str, message: types.Message, state: FSMContext):
    """Completes the registration by storing user data and sending confirmation."""
    await add_user(user_id, user_name, phone)
    user_data = await get_user_by_id(user_id)

    if user_data is None:
        await message.answer("Error: Failed to register user.")
        return

    user: User = user_data
    await message.answer(
        f"Registration Successful! Your entered details:\nName: {user.name}\nPhone: {user.phone}",
    )
    await state.set_state(RegistrationStates.registered)


@registration_router.message(RegistrationStates.awaiting_name)
async def handle_name(message: types.Message, state: FSMContext):
    # TODO: ADD DOCSTRING
    if message.from_user is None:
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return

    user_id = message.from_user.id
    name = message.text

    if not name:
        await message.answer("Имя не может быть пустым. Пожалуйста, введите ваше имя.")
        return

    await _store_temp_user_data(user_id, "name", name)
    await message.answer(f"Прекрасно, {name}! Теперь введите свой номер телефона.")
    await state.set_state(RegistrationStates.awaiting_phone)


@registration_router.message(RegistrationStates.awaiting_phone)
async def handle_phone(message: types.Message, state: FSMContext):
    # TODO: ADD DOCSTRING
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

    await _store_temp_user_data(user_id, "phone", phone)
    user_name = await _get_user_name(user_id)
    await _complete_registration(user_id, user_name, phone, message, state)


async def _is_valid_phone(phone: str) -> bool:
    """Validates the phone number."""
    number_regex = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    return bool(re.match(number_regex, phone))


async def _store_temp_user_data(user_id: int, field: str, temp_value: str):
    """Stores temporary user data."""
    temp_database_manager = TempDatabaseManager()
    await temp_database_manager.set_user_temp_value_by_name(user_id, field, temp_value)


async def _get_user_name(user_id: int) -> str:
    """Retrieves the user's name from temporary storage."""
    temp_database_manager = TempDatabaseManager()
    return await temp_database_manager.get_user_temp_value_by_name(user_id, "name")