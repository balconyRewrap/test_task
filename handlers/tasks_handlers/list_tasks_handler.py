"""
This module provides handlers for listing and managing tasks using the aiogram framework.

Handlers:
    list_task_handler: Handles the listing of tasks for a user.
    task_is_completed_handler: Handles the completion of a task when a callback query is received.
    next_page_button_handler: Handles the callback query for navigating to the next page of tasks.
    prev_page_button_handler: Handles the callback query for navigating to the previous page of tasks.

Helper Functions:
    _fetch_user_id: Fetches the user ID from the provided message or uses the given callback ID.
    _generate_keyboard: Generates an inline keyboard for task management.
    _send_or_edit_message: Sends or edits a message based on the presence of a user callback ID.
"""
from typing import Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.database_manager import get_not_completed_tasks_by_user_id, mark_task_completed
from database.models import Task
from handlers.basic_handlers.basic_keyboard import give_menu_keyboard
from handlers.basic_handlers.basic_state import start_menu
from handlers.tasks_handlers.tasks_utils import (
    get_total_pages_from_tasks_by_page_size,
    paginate_tasks,
    prepare_tasks_text,
)

list_tasks_router: Router = Router()


@list_tasks_router.message(start_menu, F.text.casefold() == "просмотр задач")
async def list_task_handler(  # noqa: WPS217
    message: Message,
    state: FSMContext,
    user_callback_id: Optional[int] = None,
) -> None:
    """
    Handles the listing of tasks for a user.

    This asynchronous function fetches the user ID, retrieves the user's not completed tasks,
    paginates them, and sends or edits a message with the tasks list and a keyboard for navigation.

    Args:
        message (Message): The message object from the user.
        state (FSMContext): The finite state machine context for the user.
        user_callback_id (Optional[int], optional): The callback ID of the user. Defaults to None.

    Returns:
        None
    """
    user_id = await _fetch_user_id(message, user_callback_id)

    if not user_id:
        return
    message.answer(
        "Поиск задач производиться. Пожалуйста, подождите",
        reply_markup=await give_menu_keyboard(user_id),
        parse_mode="HTML",
    )
    tasks = await get_not_completed_tasks_by_user_id(user_id)
    if not tasks:
        await message.answer("У вас нет задач.", reply_markup=await give_menu_keyboard(user_id))
        return

    state_data = await state.get_data()

    current_page = state_data.get("page_basic_list", 0)
    page_size = 5
    total_pages = await get_total_pages_from_tasks_by_page_size(tasks, page_size)
    await state.update_data(last_page_basic_list=total_pages - 1)

    tasks_for_page = await paginate_tasks(tasks, current_page, page_size)
    tasks_text = await prepare_tasks_text(tasks_for_page)
    is_single_page = total_pages == 1
    keyboard = await _generate_keyboard(tasks_for_page, current_page, total_pages, is_single_page)

    is_called_from_callback = bool(user_callback_id)
    await _send_or_edit_message(
        message,
        tasks_text,
        InlineKeyboardMarkup(inline_keyboard=keyboard),
        is_called_from_callback,
    )

    await state.update_data(page=current_page)
    await state.set_state(start_menu)


@list_tasks_router.callback_query(start_menu, F.data.startswith("task_is_completed"))
async def task_is_completed_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Handles the completion of a task when a callback query is received.

    Args:
        callback_query (CallbackQuery): The callback query object containing the data.
        state (FSMContext): The current state of the finite state machine.
    Behavior:
        - Extracts the task ID from the callback query data.
        - Marks the task as completed.
        - Sends a confirmation message to the user.
        - Calls the list_task_handler to update the task list.
    Raises:
        ValueError: If the callback query data is invalid.
    """
    if callback_query.data:
        # get task_id from callback_data
        task_id = int(callback_query.data.split(":")[1])
    else:
        await callback_query.answer("Ошибка: некорректные данные.", show_alert=True)
        return

    await mark_task_completed(task_id)

    await callback_query.answer("Задача отмечена выполненной", show_alert=True)

    await list_task_handler(callback_query.message, state=state, user_callback_id=callback_query.from_user.id)


@list_tasks_router.callback_query(F.data == "next_page")
async def next_page_button_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Handles the callback query for navigating to the next page of tasks.

    This function retrieves the current page and last page from the state data.
    If the current page is the last page, it resets the page to 0. Otherwise, it increments the current page by 1.
    After updating the page, it calls the list_task_handler to display the tasks for the new page.

    Args:
        callback_query (CallbackQuery):
        The callback query object containing information about the user's interaction.
        state (FSMContext): The finite state machine context for storing and retrieving state data.
    """
    user_id = callback_query.from_user.id
    state_data = await state.get_data()
    current_page = state_data.get("page_basic_list", 0)
    last_page = state_data.get("last_page_basic_list", 0)
    if current_page == last_page:
        await state.update_data(page_basic_list=0)
    else:
        await state.update_data(page_basic_list=current_page + 1)

    await list_task_handler(callback_query.message, state, user_id)


@list_tasks_router.callback_query(F.data == "prev_page")
async def prev_page_button_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Handles the callback query for navigating to the previous page of tasks.

    This function retrieves the current page number from the state data and updates it to the previous page.
    If the current page is the first page (page 0), it wraps around to the last page.
    After updating the page number in the state, it calls the `list_task_handler`
    to display the tasks for the updated page.

    Args:
        callback_query (CallbackQuery):
        The callback query object containing information about the user's interaction.
        state (FSMContext): The finite state machine context for storing and retrieving state data.
    """
    user_id = callback_query.from_user.id
    state_data = await state.get_data()
    current_page = state_data.get("page_basic_list", 0)
    last_page = state_data.get("last_page_basic_list", 0)

    if current_page == 0:
        await state.update_data(page_basic_list=last_page)
    else:
        await state.update_data(page_basic_list=current_page - 1)

    await list_task_handler(callback_query.message, state, user_id)


async def _fetch_user_id(message: Message, user_callback_id: Optional[int]) -> Optional[int]:
    """
    Fetches the user ID from the provided message or uses the given callback ID.

    Args:
        message (Message): The message object containing user information.
        user_callback_id (Optional[int]): An optional user callback ID.

    Returns:
        Optional[int]: The user ID if found, otherwise None.
    """
    if user_callback_id:
        return user_callback_id
    if message.from_user:
        return message.from_user.id
    await message.answer("Ошибка: не удалось получить информацию о пользователе.")
    return None


async def _generate_keyboard(
    tasks: list[Task],
    current_page: int,
    total_pages: int,
    is_single_page: bool,
) -> list[list[InlineKeyboardButton]]:
    """
    Generates an inline keyboard for task management.

    Args:
        tasks (list[Task]): A list of Task objects to generate buttons for.
        current_page (int): The current page number.
        total_pages (int): The total number of pages.

    Returns:
        list[list[InlineKeyboardButton]]: A 2D list representing the inline keyboard.
    """
    keyboard = []
    task_number_on_page = 1
    for task_item in tasks:
        task_text = f"Задача №{task_number_on_page} выполнена"
        task_buttons = [
            InlineKeyboardButton(text=task_text, callback_data=f"task_is_completed:{task_item.id}"),
        ]
        task_number_on_page += 1
        keyboard.append(task_buttons)
    if not is_single_page:
        navigator_button = [InlineKeyboardButton(text="Просмотр страниц", callback_data="noop")]
        keyboard.append(navigator_button)

        nav_buttons = [
            InlineKeyboardButton(text="←", callback_data="prev_page"),
            InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="current_page"),
            InlineKeyboardButton(text="→", callback_data="next_page"),
        ]
        keyboard.append(nav_buttons)

    return keyboard


async def _send_or_edit_message(
    message: Message,
    tasks_text: str,
    keyboard: InlineKeyboardMarkup,
    is_called_from_callback: bool,
) -> None:
    """
    Send or edit a message based on the presence of a user callback ID.

    Args:
        message (Message): The message object to be sent or edited.
        tasks_text (str): The text content of the message.
        keyboard (InlineKeyboardMarkup): The inline keyboard markup to be attached to the message.
        is_called_from_callback (Optional[int]):
        if called from callback - edit, else - send message

    Returns:
        None
    """
    if is_called_from_callback:
        await message.edit_text(
            text=tasks_text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        await message.answer(
            text=tasks_text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
