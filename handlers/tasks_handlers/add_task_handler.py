"""
This module contains handlers for adding tasks using the aiogram framework.

Handlers:
    add_task_handler: Handles the initiation of adding a new task by setting the state to awaiting the task name.
    handle_name: Processes the task name input from the user, validates it, and stores it in a temporary database.
    handle_tags: Processes the tags input from the user, validates them, and stores them in a temporary database.
    end_tags_callback: Handles the callback when the user ends the tag selection process,
    adds the task to the main database, and clears temporary data.

Functions:
    _create_end_tags_keyboard: Creates an inline keyboard markup with a single button to end tag input.

Dependencies:
    aiogram: Used for creating the bot and handling messages and callbacks.
    database_manager: Contains the function to add a task to the main database.
    temp_database_manager: Manages temporary storage of task data.
    handlers.basic_handlers.basic_keyboard: Provides the basic keyboard for user interaction.
    handlers.basic_handlers.basic_state: Manages the start menu state.
    handlers.tasks_handlers.tasks_states_groups: Defines the states for adding tasks.
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database_manager import add_task
from handlers.basic_handlers.basic_keyboard import give_basic_keyboard
from handlers.basic_handlers.basic_state import start_menu
from handlers.tasks_handlers.tasks_states_groups import AddTaskStates
from temp_database_manager import TempDatabaseManager

add_task_router: Router = Router()


@add_task_router.message(start_menu, F.text.casefold() == "добавить задачу")
async def add_task_handler(message: Message, state: FSMContext):
    """
    Handles the addition of a new task.

    Set the state to awaiting the task name and prompting the user to enter the task name.

    Args:
        message (Message): The message object containing the user's message.
        state (FSMContext): The finite state machine context for managing user states.
    """
    await state.set_state(AddTaskStates.awaiting_name)
    await message.answer("Введите название задачи:")


@add_task_router.message(AddTaskStates.awaiting_name)
async def handle_name(message: Message, state: FSMContext):
    """
    Handles the task name input from the user.

    This function processes the task name provided by the user, validates it, and stores it in a temporary database.
    If the task name is valid, it transitions the state to await tags input.

    Args:
        message (Message): The message object containing the user's input.
        state (FSMContext): The finite state machine context for managing user states.
    """
    if message.from_user is None:
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return

    user_id = message.from_user.id
    task_name = message.text
    if not task_name:
        await message.answer("Название задачи не может быть пустым. Пожалуйста, введите название задачи.")
        return
    temp_db = TempDatabaseManager()
    await temp_db.set_user_temp_value_by_name(user_id, "task_name", task_name)
    await state.set_state(AddTaskStates.awaiting_tags)
    await message.answer(
        "Введите теги для задачи через запятую или нажмите кнопку чтобы оставить теги пустыми:",
        reply_markup=await _create_end_tags_keyboard(),
    )


@add_task_router.message(AddTaskStates.awaiting_tags)
async def handle_tags(message: Message, state: FSMContext):
    """
    Handles the addition of tags to a task.

    This asynchronous function processes a message containing a tag for a task.
    It validates the user information and the tag, then adds the tag to the task in a temporary database.
    If the tag is successfully added, it prompts the user to enter another tag or finish the process.

    Args:
        message (Message): The message object containing the tag text and user information.
        state (FSMContext): The finite state machine context for managing user states.
    """
    if message.from_user is None:
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return

    user_id = message.from_user.id
    tag = message.text
    if not tag:
        await message.answer("Тег не может быть пустым. Пожалуйста, введите тег для задачи.")
        return
    temp_db = TempDatabaseManager()
    await temp_db.add_task_tag(user_id, tag)
    await message.answer(
        "Тег задачи успешно добавлен. Пожалуйста, введите следующий тег или нажмите кнопку для окончания.",
        reply_markup=await _create_end_tags_keyboard(),
    )


@add_task_router.callback_query(lambda c: c.data == 'end_tags')
async def end_tags_callback(query: CallbackQuery, state: FSMContext):
    """
    Handles the callback when the user ends the tag selection process.

    This function retrieves the task name and tags associated with the user from a temporary database,
    adds the task to the main database, clears the user's temporary data, and sends a confirmation message
    to the user.

    Args:
        query (CallbackQuery): The callback query from the user interaction.
        state (FSMContext): The current state of the finite state machine.
    """
    user_id = query.from_user.id
    temp_db = TempDatabaseManager()
    task_name = await temp_db.get_user_temp_value_by_name(user_id, "task_name")
    tags = await temp_db.get_task_tags(user_id)
    await add_task(user_id=user_id, name=task_name, tags=tuple(tags))
    await temp_db.clear_user_data_from_redis(user_id)

    if query.message:
        await query.message.answer("Задача успешно добавлена!", reply_markup=await give_basic_keyboard())
    await state.set_state(start_menu)


async def _create_end_tags_keyboard() -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard markup with a single button to end tag input.

    Returns:
        InlineKeyboardMarkup: An inline keyboard markup containing a button labeled
        "Закончить заполнение тегов" with callback data "end_tags".
    """
    end_tags_button = [[InlineKeyboardButton(text="Закончить заполнение тегов", callback_data="end_tags")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=end_tags_button)
    return keyboard
