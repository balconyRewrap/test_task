from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database_manager import get_tasks_by_user_id
from handlers.basic_handlers.basic_keyboard import give_basic_keyboard
from handlers.basic_handlers.basic_state import start_menu
from handlers.tasks_handlers.tasks_states_groups import AddTaskStates
from temp_database_manager import TempDatabaseManager

list_tasks_router: Router = Router()

@list_tasks_router.message(start_menu, F.text.casefold() == "просмотр задач")
async def add_task_handler(message: Message, state: FSMContext):
    # TODO: ADD DOCSTRING
    if not message.from_user:
        message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return
    user_id = message.from_user.id
    tasks = await get_tasks_by_user_id(user_id)
    if not tasks:
        await message.answer("У вас нет задач.")
        return
    tasks_text = "Ваши задачи:\n"
    for task in tasks:
        tasks_text += f"{task.name}\n"
        if not task.tags:
            continue
        tasks_text += "Теги: "
        for tag in task.tags:
            tasks_text += f"{tag}, "
        tasks_text = tasks_text[:-2] + "\n"
    await message.answer(tasks_text)
    


