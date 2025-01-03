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

from database.database_manager import add_task
from handlers.basic_handlers.basic_keyboard import give_menu_keyboard, give_post_menu_keyboard
from handlers.basic_handlers.basic_state import start_menu
from handlers.tasks_handlers.tasks_states_groups import AddTaskStates

add_task_router: Router = Router()


@add_task_router.message(start_menu, F.text.casefold() == "добавить задачу")
async def add_task_handler(message: Message, state: FSMContext) -> None:
    """
    Handles the addition of a new task.

    Set the state to awaiting the task name and prompting the user to enter the task name.

    Args:
        message (Message): The message object containing the user's message.
        state (FSMContext): The finite state machine context for managing user states.
    """
    await state.set_state(AddTaskStates.waiting_name)
    await message.answer("Введите название <b>задачи</b>:", reply_markup=await give_post_menu_keyboard())


@add_task_router.message(AddTaskStates.waiting_name)
async def handle_name(message: Message, state: FSMContext) -> None:
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

    task_name = message.text
    if not task_name:
        await message.answer("Название задачи не может быть пустым. Пожалуйста, введите название задачи.")
        return
    await _clean_state(state)
    await state.update_data(task_name=task_name)
    await state.set_state(AddTaskStates.waiting_tags)
    await message.answer(
        "Введите <b>теги</b> для задачи через запятую, через <b>enter</b> или нажмите кнопку <b>'Закончить заполнение тегов'</b> чтобы оставить теги пустыми:",  # noqa: E501
        reply_markup=await _create_end_tags_keyboard(),
    )


@add_task_router.message(AddTaskStates.waiting_tags)
async def handle_tags(message: Message, state: FSMContext) -> None:
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

    tag = message.text
    if not tag:
        await message.answer("Тег не может быть пустым. Пожалуйста, введите тег для задачи.")
        return
    state_data = await state.get_data()
    existed_tags: list = state_data.get("tags", [])
    existed_tags.append(tag)
    await state.update_data(tags=existed_tags)
    answer_text = (
        "Тег успешно добавлен. Пожалуйста, введите "
        "следующий тег или нажмите кнопку <b>'Закончить заполнение тегов'</b> для окончания."
    )
    await message.answer(
        answer_text,
        reply_markup=await _create_end_tags_keyboard(),
    )


@add_task_router.callback_query(F.data == 'end_tags')
async def end_tags_callback(query: CallbackQuery, state: FSMContext) -> None:
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
    state_data = await state.get_data()
    task_name = state_data.get("task_name")
    tags = state_data.get("tags", [])
    if not task_name:
        await query.answer("Ошибка: название задачи не найдено.")
        return
    await add_task(user_id=user_id, name=task_name, tags=tuple(tags))
    await _clean_state(state)
    if query.message:
        await query.message.answer("Задача успешно добавлена!", reply_markup=await give_menu_keyboard(user_id))
    # await state.clear()
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


async def _clean_state(state: FSMContext) -> None:
    """
    Cleans the state by removing all data stored in the state.

    Args:
        state (FSMContext): The finite state machine context for managing user states.
    """
    await state.set_data(data={"task_name": ""})
    await state.set_data(data={"tags": []})
