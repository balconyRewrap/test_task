"""
This module defines a defaul message handler for an aiogram-based bot.

Attributes:
    basic_router (Router): An instance of aiogram's Router used to register message handlers.

Functions:
    handle_all_other_messages(message: types.Message):
"""
from aiogram import Router, types
from aiogram.fsm.context import FSMContext

default_router: Router = Router()


@default_router.message()
async def handle_all_other_messages(message: types.Message, state: FSMContext) -> None:
    """
    Handles all messages that do not match any specific command.

    Args:
        message (types.Message): The message object containing the details of the received message.
    Returns:
        None: This function sends a response message to the user indicating that the command is not recognized.
    """
    await state.clear()
    await message.answer("Команда не распознана.\nПожалуйста, используйте /start или кнопки ниже.")
