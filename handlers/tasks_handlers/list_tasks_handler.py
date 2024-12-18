"""
This module provides handlers for listing and managing tasks using the aiogram library.

Handlers:
- list_task_handler: Handles the listing of tasks for a user.
- task_is_completed_handler: Handles the completion of a task when a callback query is received.
- next_page_handler: Handles the callback query for navigating to the next page of tasks.
- prev_page_handler: Handles the callback query for navigating to the previous page of tasks.

Helper Functions:
- _fetch_user_id: Fetches the user ID from the provided message or uses the given callback ID.
- _get_total_pages_from_tasks_by_page_size: Calculates the total number of pages required to display all tasks.
- _prepare_tasks_text: Asynchronously prepares a formatted text representation of a list of tasks.
- _generate_keyboard: Generates an inline keyboard for task management.
- _paginate_tasks: Paginates a list of tasks.
"""
from typing import Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database_manager import get_not_completed_tasks_by_user_id, mark_task_completed
from handlers.basic_handlers.basic_state import start_menu
from models import Task

list_tasks_router: Router = Router()


@list_tasks_router.message(start_menu, F.text.casefold() == "просмотр задач")
async def list_task_handler(message: Message, state: FSMContext, user_callback_id: Optional[int] = None):
    """
    Handles the listing of tasks for a user.

    This asynchronous function fetches the user ID, retrieves the user's not completed tasks,
    paginates them, and sends the tasks to the user in a message. If a user callback ID is provided,
    the message is edited; otherwise, a new message is sent.

    Args:
        message (Message): The message object from the user.
        state (FSMContext): The finite state machine context for the user.
        user_callback_id (Optional[int], optional): The callback ID for the user. Defaults to None.
    """
    user_id = await _fetch_user_id(message, user_callback_id)
    if not user_id:
        return

    tasks = await get_not_completed_tasks_by_user_id(user_id)
    if not tasks:
        await message.answer("У вас нет задач.")
        return

    state_data = await state.get_data()
    current_page = state_data.get("page", 0)
    page_size = 5
    total_pages = await _get_total_pages_from_tasks_by_page_size(tasks, page_size)

    if "last_page" not in state_data:
        last_page = total_pages - 1
        await state.update_data(last_page=last_page)

    tasks_for_page = await _paginate_tasks(tasks, current_page, page_size)

    tasks_text = await _prepare_tasks_text(tasks_for_page)
    keyboard = await _generate_keyboard(tasks_for_page, current_page, total_pages)

    if user_callback_id:
        await message.edit_text(
            text=tasks_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        )
    else:
        await message.answer(
            text=tasks_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        )

    await state.update_data(page=current_page)


@list_tasks_router.callback_query(F.data.startswith("task_is_completed"))
async def task_is_completed_handler(callback_query: CallbackQuery, state: FSMContext):
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
async def next_page_handler(callback_query: CallbackQuery, state: FSMContext):
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
    current_page = state_data.get("page", 0)
    last_page = state_data.get("last_page", 0)

    if current_page == last_page:
        await state.update_data(page=0)
    else:
        await state.update_data(page=current_page + 1)

    await list_task_handler(callback_query.message, state, user_id)


@list_tasks_router.callback_query(F.data == "prev_page")
async def prev_page_handler(callback_query: CallbackQuery, state: FSMContext):
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
    current_page = state_data.get("page", 0)

    last_page = state_data.get("last_page", 0)

    if current_page == 0:
        await state.update_data(page=last_page)
    else:
        await state.update_data(page=current_page - 1)

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


async def _get_total_pages_from_tasks_by_page_size(tasks: list[Task], page_size: int) -> int:
    """
    Calculates the total number of pages required to display all tasks.

    Args:
        tasks (list[Task]): A list of Task objects to be paginated.
        page_size (int): The number of tasks per page.

    Returns:
        int: The total number of pages required to display all tasks.
    """
    return (len(tasks) + page_size - 1) // page_size


async def _prepare_tasks_text(tasks: list[Task]) -> str:
    """
    Asynchronously prepares a formatted text representation of a list of tasks.

    Args:
        tasks (list[Task]): A list of Task objects to be formatted.

    Returns:
        str: A formatted string representing the list of tasks, including their names and tags.
    """
    tasks_text = "<b>Ваши задачи:</b>\n"
    for task in tasks:
        tasks_text += f"• <b>{task.name}</b>\n"  # noqa: WPS336
        if task.tags:
            tasks_text += "<i>Теги:</i>\n    ◦ "  # noqa: WPS336
            tasks_text += f"{'\n    ◦ '.join([f'<code>{tag}</code>' for tag in task.tags])}\n"  # noqa: WPS221, WPS336, E501
    return tasks_text


async def _generate_keyboard(
    tasks: list[Task],
    current_page: int,
    total_pages: int,
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

    for task_item in tasks:
        task_buttons = [
            InlineKeyboardButton(text=f"{task_item.name}", callback_data="noop"),
            InlineKeyboardButton(text="Выполнена", callback_data=f"task_is_completed:{task_item.id}"),
        ]
        keyboard.append(task_buttons)

    navigator_button = [InlineKeyboardButton(text="Навигация по страницам", callback_data="noop")]
    keyboard.append(navigator_button)

    nav_buttons = [
        InlineKeyboardButton(text="←", callback_data="prev_page"),
        InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="current_page"),
        InlineKeyboardButton(text="→", callback_data="next_page"),
    ]
    keyboard.append(nav_buttons)

    return keyboard


async def _paginate_tasks(tasks: list[Task], current_page: int, page_size: int) -> list[Task]:
    """
    Paginate a list of tasks.

    Args:
        tasks (list[Task]): The list of tasks to paginate.
        current_page (int): The current page number (0-indexed).
        page_size (int): The number of tasks per page.
    Returns:
        list[Task]: A sublist of tasks for the specified page.
    """
    start = current_page * page_size
    end = start + page_size
    return tasks[start:end]
