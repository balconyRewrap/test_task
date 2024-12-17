# TODO: ADD DOCSTRING
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
    # TODO: ADD DOCSTRING
    await state.set_state(AddTaskStates.awaiting_name)
    await message.answer("Введите название задачи:")


@add_task_router.message(AddTaskStates.awaiting_name)
async def handle_name(message: Message, state: FSMContext):
    # TODO: ADD DOCSTRING
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
    # TODO: ADD DOCSTRING
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
    # TODO: ADD DOCSTRING
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
    end_tags_button = [[InlineKeyboardButton(text="Закончить заполнение тегов", callback_data="end_tags")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=end_tags_button)
    return keyboard
