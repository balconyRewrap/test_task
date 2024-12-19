"""
This module provides functionality to generate a basic reply keyboard markup for a player using the aiogram library.

Functions:
    give_basic_keyboard() -> types.ReplyKeyboardMarkup:

    _give_basic_buttons() -> list[list[types.KeyboardButton]]:
        Asynchronously generates a list of basic keyboard buttons.
"""
from aiogram import types


async def give_basic_keyboard() -> types.ReplyKeyboardMarkup:
    """
    Asynchronously generates a basic reply keyboard markup for a player.

    Args:
        player_id (str): The ID of the player for whom the keyboard is being generated.
    Returns:
        types.ReplyKeyboardMarkup: An instance of ReplyKeyboardMarkup containing the basic keyboard layout.
    """
    basic_keyboard = await _give_basic_buttons()
    basic_reply_keyboard_markup = types.ReplyKeyboardMarkup(keyboard=basic_keyboard, resize_keyboard=True)
    return basic_reply_keyboard_markup


async def _give_basic_buttons() -> list[list[types.KeyboardButton]]:
    basic_buttons: list[list[types.KeyboardButton]] = []
    add_task_button = types.KeyboardButton(text="Добавить задачу")
    view_tasks_button = types.KeyboardButton(text="Просмотр задач")
    search_tasks_button = types.KeyboardButton(text="Поиск задач")
    main_menu_button = types.KeyboardButton(text="Главное меню")
    basic_buttons.append([add_task_button])
    basic_buttons.append([view_tasks_button])
    basic_buttons.append([search_tasks_button])
    basic_buttons.append([main_menu_button])
    return basic_buttons
