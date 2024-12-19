"""
This module provides functions to generate reply keyboard markups for a Telegram bot using the aiogram library.

Functions:
    give_menu_keyboard() -> types.ReplyKeyboardMarkup:

    give_post_menu_keyboard() -> types.ReplyKeyboardMarkup:
        Asynchronously generates a reply keyboard markup for the post menu,
        including a "Главное меню" (Main Menu) button.

    _give_basic_buttons() -> list[list[types.KeyboardButton]]:
        Asynchronously generates a list of basic keyboard buttons for the reply keyboard markup.
"""
from aiogram import types

from database.database_manager import has_any_task_by_user_id


async def give_menu_keyboard(user_id: int) -> types.ReplyKeyboardMarkup:
    """
    Asynchronously generates a basic reply keyboard markup for a player.

    Args:
        player_id (str): The ID of the player for whom the keyboard is being generated.
    Returns:
        types.ReplyKeyboardMarkup: An instance of ReplyKeyboardMarkup containing the basic keyboard layout.
    """
    basic_keyboard = await _give_basic_buttons(user_id)
    basic_reply_keyboard_markup = types.ReplyKeyboardMarkup(keyboard=basic_keyboard, resize_keyboard=True)
    return basic_reply_keyboard_markup


async def give_post_menu_keyboard() -> types.ReplyKeyboardMarkup:
    """
    Asynchronously creates and returns a ReplyKeyboardMarkup object with a main menu button.

    Returns:
        types.ReplyKeyboardMarkup: A keyboard markup object containing a single button labeled "Главное меню".
    """
    main_menu_button = types.KeyboardButton(text="Главное меню")

    basic_keyboard: list[list[types.KeyboardButton]] = []
    basic_keyboard.append([main_menu_button])
    basic_reply_keyboard_markup = types.ReplyKeyboardMarkup(keyboard=basic_keyboard, resize_keyboard=True)
    return basic_reply_keyboard_markup


async def _give_basic_buttons(user_id: int) -> list[list[types.KeyboardButton]]:
    basic_buttons: list[list[types.KeyboardButton]] = []
    
    add_task_button = types.KeyboardButton(text="Добавить задачу")
    basic_buttons.append([add_task_button])
    if await has_any_task_by_user_id(user_id):
        view_tasks_button = types.KeyboardButton(text="Просмотр задач")
        search_tasks_button = types.KeyboardButton(text="Поиск задач")
        basic_buttons.append([view_tasks_button])
        basic_buttons.append([search_tasks_button])

    return basic_buttons
