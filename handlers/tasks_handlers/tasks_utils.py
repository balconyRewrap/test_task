"""
This module provides utility functions for handling and paginating tasks.

Functions:
    get_total_pages_from_tasks_by_page_size(tasks: list[Task], page_size: int) -> int:

    paginate_tasks(tasks: list[Task], current_page: int, page_size: int) -> list[Task]:
        Paginates a list of tasks.

    prepare_tasks_text(tasks: list[Task]) -> str:
"""
from database.models import Task


async def get_total_pages_from_tasks_by_page_size(tasks: list[Task], page_size: int) -> int:
    """
    Calculates the total number of pages required to display all tasks.

    Args:
        tasks (list[Task]): A list of Task objects to be paginated.
        page_size (int): The number of tasks per page.

    Returns:
        int: The total number of pages required to display all tasks.
    """
    return (len(tasks) + page_size - 1) // page_size


async def paginate_tasks(tasks: list[Task], current_page: int, page_size: int) -> list[Task]:
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


async def prepare_tasks_text(tasks: list[Task]) -> str:
    """
    Asynchronously prepares a formatted text representation of a list of tasks.

    Args:
        tasks (list[Task]): A list of Task objects to be formatted.

    Returns:
        str: A formatted string representing the list of tasks, including their names and tags.
    """
    tasks_text = "<b>Ваши задачи:</b>"
    task_number_on_page = 1
    for task in tasks:
        tasks_text += f"\n{task_number_on_page}. <b>{task.name}</b>\n"
        task_number_on_page += 1
        if task.tags:
            tasks_text += "<i>Теги:</i>\n    ◦ "
            tasks_text += f"{'\n    ◦ '.join([f'<code>{tag}</code>' for tag in task.tags])}\n"  # noqa: WPS221, E501
    return tasks_text
