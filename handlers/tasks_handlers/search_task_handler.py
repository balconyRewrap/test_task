"""
This module defines the handlers for searching tasks using the aiogram library.

Handlers:
- search_task_handler: Initiates the task search process based on user input.
- handle_query: Processes the user's query input during the task search.
- handle_tags: Processes the user's tags input during the task search.
- search_tags_button_handler: Handles the callback query for the search tags button.
- search_query_button_handler: Handles the callback query for the search query button.
- end_search_button_handler: Handles the 'end search' button press during the task search.
- end_task_list_button_handler: Handles the 'end task list' button press during the task search.
- next_page_button_handler: Handles the callback query for navigating to the next page of tasks.
- prev_page_button_handler: Handles the callback query for navigating to the previous page of tasks.

Helper Functions:
- _handle_list_tasks: Manages the listing of tasks based on the user's search criteria.
- _get_search_criteria: Extracts search criteria from the given state data.
- _search_tasks_or_handle_error: Searches for tasks based on provided keywords and tags, or handles errors.
- _handle_no_tasks_found: Manages the scenario when no tasks are found based on the given criteria.
- _display_tasks: Displays a paginated list of tasks in a message.
- _create_search_tasks_keyboard:
Creates an inline keyboard for search tasks based on the current state and pagination.
- _generate_keyboard: Generates an inline keyboard for task management.
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.database_manager import search_tasks
from handlers.basic_handlers.basic_keyboard import give_basic_keyboard
from handlers.basic_handlers.basic_state import start_menu
from handlers.tasks_handlers.tasks_states_groups import SearchStates
from handlers.tasks_handlers.tasks_utils import (
    get_total_pages_from_tasks_by_page_size,
    paginate_tasks,
    prepare_tasks_text,
)
from database.models import Task

search_tasks_router: Router = Router()


@search_tasks_router.message(start_menu, F.text.casefold().startswith("поиск задач"))
async def search_task_handler(message: Message, state: FSMContext) -> None:
    """
    Handles the search of tasks based on user input.

    Args:
        message (Message): The message object from the user.
        state (FSMContext): The state object for tracking user sessions.
    """
    if message.from_user is None:
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return

    answer_text = (
        "<b>Поиск задач</b>\n\n"
        "Для поиска по ключевым словам введите их через запятую или нажмите Enter для каждого нового слова."
        "Если вы хотите искать задачи по одному слову, просто введите его."
        "Для поиска по тегам, нажмите на кнопку ниже, и вы сможете ввести теги для поиска задач."
        "Для окончания поиска нажмите кнопку 'Закончить поиск'."
    )

    await state.set_state(SearchStates.waiting_for_query)
    reply_markup = await _create_search_tasks_keyboard(state)
    if not reply_markup:
        await message.answer("К сожалению, произошла ошибка. Попробуйте еще раз.")

    await message.answer(answer_text, reply_markup=reply_markup)


@search_tasks_router.message(SearchStates.waiting_for_query)
async def handle_query(message: Message, state: FSMContext) -> None:
    """
    Handles the user's query input during the task search process.

    Args:
        message (Message): The message object containing the user's input.
        state (FSMContext): The finite state machine context for managing user states.
    """
    if message.from_user is None:
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return

    query = message.text
    if not query:
        await message.answer(
            "Ключевые слова не могут быть пустыми. Пожалуйста, введите ключевые слова для поиска "
            "или используйте кнопку тегов.",
        )
        return

    if ',' in query:
        keywords = [word.strip() for word in query.split(',')]
    else:
        keywords = [query.strip()]

    state_data = await state.get_data()
    existing_keywords = state_data.get("keywords", [])
    keywords = existing_keywords + keywords

    await state.update_data(keywords=keywords)
    answer_text = (
        f"Ключевые слова для поиска: {', '.join(keywords)}\n"
        "Продолжайте вводить ключевые слова или нажмите кнопку для поиска по тегам.\n"
        "Для окончания поиска нажмите кнопку 'Закончить поиск'.\n"
    )

    await message.answer(answer_text)


@search_tasks_router.message(SearchStates.waiting_for_tags)
async def handle_tags(message: Message, state: FSMContext) -> None:
    """
    Handles the user's tags input during the task search process.

    Args:
        message (Message): The message object containing the user's input.
        state (FSMContext): The finite state machine context for managing user states.
    """
    if message.from_user is None:
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return

    tags = message.text
    if not tags:
        await message.answer(
            "Теги не могут быть пустыми. Пожалуйста, "
            "введите ключевые теги для поиска или используйте кнопку ключевых слов.",
        )
        return

    if ',' in tags:
        tags = [word.strip() for word in tags.split(',')]
    else:
        tags = [tags.strip()]

    state_data = await state.get_data()
    existing_tags = state_data.get("tags", [])
    if not isinstance(existing_tags, list):
        existing_tags = []
    tags = existing_tags + tags

    await state.update_data(tags=tags)
    answer_text = (
        f"Теги для поиска: {', '.join(tags)}\n"
        "Продолжайте вводить ключевые слова или нажмите кнопку для поиска по тегам.\n"
        "Для окончания поиска нажмите кнопку 'Закончить поиск'.\n"
    )

    await message.answer(answer_text)


@search_tasks_router.callback_query(F.data == "search_tags")
async def search_tags_button_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Handles the callback query for the search tags button.

    This function is triggered when the user presses the button to search tasks by tags.
    It sends a message to the user with instructions on how to enter tags for the search.
    The user can enter tags separated by commas or one tag per line by pressing Enter.
    The function also provides options to switch to keyword search or to end the search.

    Args:
        callback_query (CallbackQuery): The callback query from the user interaction.
        state (FSMContext): The current state of the finite state machine.
    Returns:
        None
    """
    answer_text = (
        "<b>Поиск задач по тегам</b>\n\n"
        "Введите теги для поиска задач через запятую или нажмите Enter для каждого нового тега."
        "Для перехода в поиск по ключевым словам нажмите кнопку 'Поиск по ключевым словам'."
        "Для окончания поиска нажмите кнопку 'Закончить поиск'."
    )
    await state.set_state(SearchStates.waiting_for_tags)
    if callback_query.message:
        await callback_query.message.answer(answer_text)


@search_tasks_router.callback_query(F.data == "search_query")
async def search_query_button_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Handles the callback query for the search query button.

    This function sends a message to the user with instructions on how to search for tasks by query.
    It sets the state to waiting_for_query to indicate that the bot is waiting for the user to input search query.

    Args:
        callback_query (CallbackQuery): The callback query from the user.
        state (FSMContext): The current state of the finite state machine.
    Returns:
        None
    """
    answer_text = (
        "<b>Поиск задач по тегам</b>\n\n"
        "Введите теги для поиска задач через запятую или нажмите Enter для каждого нового тега."
        "Для перехода в поиск по ключевым словам нажмите кнопку 'Поиск по ключевым словам'."
        "Для окончания поиска нажмите кнопку 'Закончить поиск'."
    )
    await state.set_state(SearchStates.waiting_for_query)
    if callback_query.message:
        await callback_query.message.answer(answer_text)


@search_tasks_router.callback_query(F.data == "end_search")
async def end_search_button_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Handles the 'end search' button press during the task search process.

    Args:
        callback_query (CallbackQuery): The callback query object containing the user's input.
        state (FSMContext): The finite state machine context for managing user states.
    """
    user_id = callback_query.from_user.id
    await state.set_state(SearchStates.listing_tasks)
    if not callback_query.message:
        return
    await callback_query.message.answer("Поиск задач завершен.")
    if isinstance(callback_query.message, Message):
        await _handle_list_tasks(callback_query.message, state, user_id, called_after_search=True)


@search_tasks_router.callback_query(F.data == "end_task_list")
async def end_task_list_button_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Handles the 'end search' button press during the task search process.

    Args:
        callback_query (CallbackQuery): The callback query object containing the user's input.
        state (FSMContext): The finite state machine context for managing user states.
    """
    await state.clear()
    await state.set_state(start_menu)
    await callback_query.answer("Показ задач завершен.", reply_markup=await give_basic_keyboard())


@search_tasks_router.callback_query(F.data == "next_page_search")
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
    current_page = state_data.get("page_search_list", 0)
    last_page = state_data.get("last_page_search_list", 0)

    if current_page == last_page:
        await state.update_data(page_search_list=0)
    else:
        await state.update_data(page_search_list=current_page + 1)
    await state.set_state(SearchStates.listing_tasks)
    if isinstance(callback_query.message, Message):
        await _handle_list_tasks(callback_query.message, state, user_id)


@search_tasks_router.callback_query(F.data == "prev_page_search")
async def prev_page_button_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Handles the callback query for navigating to the previous page of tasks.

    This function retrieves the current page number from the state data and updates it to the previous page.
    If the current page is the first page (page 0), it wraps around to the last page.
    After updating the page, it calls the list_task_handler to display the tasks for the previous page.

    Args:
        callback_query (CallbackQuery):
        The callback query object containing information about the user's interaction.
        state (FSMContext): The finite state machine context for storing and retrieving state data.
    """
    user_id = callback_query.from_user.id

    await state.set_state(SearchStates.listing_tasks)
    user_id = callback_query.from_user.id
    state_data = await state.get_data()
    current_page = state_data.get("page_search_list", 0)
    last_page = state_data.get("last_page_search_list", 0)

    if current_page == 0:
        await state.update_data(page_search_list=last_page)
    else:
        await state.update_data(page_search_list=current_page - 1)
    if isinstance(callback_query.message, Message):
        await _handle_list_tasks(callback_query.message, state, user_id)


async def _handle_list_tasks(
    message: Message,
    state: FSMContext,
    user_callback_id: int,
    called_after_search: bool = False,
) -> None:
    """
    Handles the listing of tasks based on the user's search criteria.

    Args:
        message (Message): The message object containing user information and message details.
        state (FSMContext): The finite state machine context for managing user states.
        user_callback_id (int): The ID of the user callback.
        called_after_search (bool, optional): Flag indicating if the function is called after a search.
        Defaults to False.
    Returns:
        None
    """
    if message.from_user is None:
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return

    keywords, tags = await _get_search_criteria(state)

    try:
        tasks = await _search_tasks_or_handle_error(message, state, user_callback_id, keywords, tags)
    except ValueError:
        return

    if not tasks:
        await _handle_no_tasks_found(message, state)
        return

    await _display_tasks(message, state, tasks, called_after_search)


async def _get_search_criteria(state: FSMContext) -> tuple[list[str], list[str]]:
    """
    Extracts search criteria from the given state data.

    Args:
        state_data (dict): A dictionary containing the state data with potential keys "keywords" and "tags".

    Returns:
        tuple[list[str], list[str]]: A tuple containing two lists:
            - The first list contains the keywords.
            - The second list contains the tags.
    """
    state_data = await state.get_data()
    keywords = state_data.get("keywords", [])
    tags = state_data.get("tags", [])
    # clean the memory after other searches
    if keywords or tags:
        await state.set_data(data={"keywords_and_tags": ()})
        await state.set_data(data={"keywords": []})
        await state.set_data(data={"tags": []})
        await state.update_data(keywords_and_tags=(keywords, tags))
    else:
        keywords, tags = state_data.get("keywords_and_tags", ([], []))

    return keywords, tags


async def _search_tasks_or_handle_error(
    message: Message,
    state: FSMContext,
    user_callback_id: int,
    keywords: list[str],
    tags: list[str],
) -> list[Task]:
    """
    Asynchronously searches for tasks based on provided keywords and tags, or handles errors if they occur.

    Args:
        message (Message): The message object to send responses to the user.
        state (FSMContext): The finite state machine context for managing user states.
        user_callback_id (int): The ID of the user callback.
        keywords (list[str]): A list of keywords to search for.
        tags (list[str]): A list of tags to search for.

    Returns:
        list[Task]: A list of tasks that match the search criteria.

    Raises:
        ValueError: If both keywords and tags are empty,
        an error message is sent to the user, the state is cleared, and the state is set to the start menu.
    """
    try:
        tasks = await search_tasks(user_callback_id, keywords, tags)
    except ValueError:
        await message.answer("И теги, и ключевые слова не могут быть пустыми.")
        await state.clear()
        await state.set_state(start_menu)
        raise
    return tasks


async def _handle_no_tasks_found(message: Message, state: FSMContext) -> None:
    """
    Handles the scenario when no tasks are found based on the given criteria.

    Args:
        message (Message): The message object containing the user's request.
        state (FSMContext): The finite state machine context for managing conversation state.

    Returns:
        None
    """
    await message.answer("Задачи, соответствующие заданным критериям, не найдены.")
    await state.clear()
    await state.set_state(start_menu)


async def _display_tasks(
    message: Message,
    state: FSMContext,
    tasks: list[Task],
    called_after_search: bool,
) -> None:
    """
    Asynchronously displays a paginated list of tasks in a message.

    Args:
        message (Message): The message object to send or edit.
        state (FSMContext): The finite state machine context for the current user.
        tasks (list[Task]): The list of tasks to display.
        called_after_search (bool): Flag indicating if the function is called after a search.

    Returns:
        None
    """
    state_data = await state.get_data()
    current_page = state_data.get("page_search_list", 0)
    page_size = 5

    total_pages = await get_total_pages_from_tasks_by_page_size(tasks, page_size)
    last_page = total_pages - 1

    if "last_page_search_list" not in state_data:
        await state.update_data(last_page_search_list=last_page)

    tasks_for_page = await paginate_tasks(tasks, current_page, page_size)
    tasks_text = await prepare_tasks_text(tasks_for_page)

    is_single_page = total_pages == 1
    keyboard = await _generate_keyboard(tasks_for_page, current_page, total_pages, is_single_page)

    if called_after_search:
        await message.answer(
            text=tasks_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        )
    else:
        await message.edit_text(
            text=tasks_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        )

    await state.update_data(page=current_page)
    await state.set_state(start_menu)


async def _create_search_tasks_keyboard(
    state: FSMContext,
    current_page: int = 0,
    total_pages: int = 0,
) -> InlineKeyboardMarkup | None:
    """
    Creates an inline keyboard for search tasks based on the current state and pagination.

    Args:
        state (FSMContext): The current state of the finite state machine.
        current_page (int, optional): The current page number for pagination. Defaults to 0.
        total_pages (int, optional): The total number of pages for pagination. Defaults to 0.
    Returns:
        InlineKeyboardMarkup | None: if state not in proper SearchStates, return None.
    """
    if not state:
        return None

    search_tasks_buttons = None
    current_state = await state.get_state()

    if current_state == SearchStates.waiting_for_query:
        search_tasks_buttons = [
            [InlineKeyboardButton(text="Поиск по тегам", callback_data="search_tags")],
            [InlineKeyboardButton(text="Закончить поиск", callback_data="end_search")],
        ]

    if current_state == SearchStates.waiting_for_tags:
        search_tasks_buttons = [
            [InlineKeyboardButton(text="Поиск по ключевым словам", callback_data="search_query")],
            [InlineKeyboardButton(text="Закончить поиск", callback_data="end_search")],
        ]

    if current_state == SearchStates.listing_tasks and all((current_page, total_pages)):
        nav_buttons = [
            InlineKeyboardButton(text="←", callback_data="prev_page"),
            InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="current_page"),
            InlineKeyboardButton(text="→", callback_data="next_page"),
        ]
        search_tasks_buttons = [
            nav_buttons,
            [InlineKeyboardButton(text="Закончить показ задач", callback_data="end_task_list")],
        ]

    if not search_tasks_buttons:

        return None

    return InlineKeyboardMarkup(inline_keyboard=search_tasks_buttons)


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

    if not is_single_page:
        navigator_button = [InlineKeyboardButton(text="Навигация по страницам", callback_data="noop")]
        keyboard.append(navigator_button)
        nav_buttons = [
            InlineKeyboardButton(text="←", callback_data="next_page_search"),
            InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="current_page"),
            InlineKeyboardButton(text="→", callback_data="prev_page_search"),
        ]
        keyboard.append(nav_buttons)

    return keyboard
