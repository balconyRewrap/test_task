# TODO: ADD DOCSTRING
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database_manager import get_user_by_id
from handlers.states_groups import RegistrationStates

start_router: Router = Router()


@start_router.message(Command('start'))
async def cmd_start(message: types.Message, state: FSMContext):
    # TODO: ADD DOCSTRING
    if message.from_user is None:
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return

    user_id = message.from_user.id
    await state.clear()
    if await get_user_by_id(user_id) is not None:
        await message.answer("Вы уже зарегистрированы.")
        return
    await state.set_state(RegistrationStates.awaiting_name)
    await message.answer("Привет! Давайте начнем регистрацию. Пожалуйста, укажите ваше имя.")
