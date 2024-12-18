"""
This module provides asynchronous database management functions for a task management system.

It includes functions to add users, add tasks, retrieve tasks, mark tasks as completed, and search tasks.
The module uses SQLAlchemy for ORM and async database operations.

Functions:
    is_env_valid() -> bool:
    add_user(user_id: int, name: str, phone: str) -> str:
    get_user_by_id(user_id: int) -> User | None:
    add_task(user_id: int, name: str, tags: Optional[Tuple[str, ...]] = None) -> str:
    get_tasks_by_user_id(user_id: int) -> list[Task]:
    get_not_completed_tasks_by_user_id(user_id: int) -> list[Task]:
    mark_task_completed(task_id: int) -> str:
    search_tasks(user_id: int, query: Optional[list[str]] = None, tags: Optional[list[str]] = None) -> list[Task]:
    init_db() -> None:
"""
from typing import Optional, Tuple

from decouple import config
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from database.models import Base, Tag, Task, User


def is_env_valid():
    """
    Validates the environment configuration by checking the presence and types of required environment variables.

    Raises:
        ValueError: If any of the required environment variables are not defined or have incorrect types.
            - "API_TOKEN" must be a string.
            - "REDIS_HOST" must be a string.
            - "REDIS_PORT" must be an integer.
            - "MARIADB_HOST" must be a string.
            - "MARIADB_USER" must be a string.
            - "MARIADB_PASSWORD" must be a string.
            - "MARIADB_DATABASE" must be a string.

    Returns:
        bool: True if all required environment variables are correctly defined.
    """
    required_variables = [
        ("API_TOKEN", str),
        ("REDIS_HOST", str),
        ("REDIS_PORT", int),
        ("MARIADB_HOST", str),
        ("MARIADB_USER", str),
        ("MARIADB_PASSWORD", str),
        ("MARIADB_DATABASE", str),
    ]

    for var_name, var_type in required_variables:
        real_var = config(var_name)
        if not isinstance(real_var, var_type):
            raise ValueError(f"{var_name} isn't defined correctly in .env")

    return True


MARIADB_USER = config("MARIADB_USER")
MARIADB_PASSWORD = config("MARIADB_PASSWORD")
MARIADB_HOST = config("MARIADB_HOST")
MARIADB_DATABASE = config("MARIADB_DATABASE")
DATABASE_URL = f"mariadb+asyncmy://{MARIADB_USER}:{MARIADB_PASSWORD}@{MARIADB_HOST}/{MARIADB_DATABASE}?charset=utf8mb4"  # noqa: WPS221, E501

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def add_user(user_id: int, name: str, phone: str) -> str:
    """
    Asynchronously adds a new user to the database.

    Args:
        user_id (int): The unique identifier for the user.
        name (str): The name of the user.
        phone (str): The phone number of the user.
    Returns:
        str: A message indicating the result of the operation.
    Raises:
        IntegrityError: If a user with the given ID already exists in the database.
    """
    async with AsyncSessionLocal() as session:
        new_user = User(id=user_id, name=name, phone=phone)
        try:
            session.add(new_user)
            await session.commit()
            return f"Пользователь {name} успешно добавлен в базу данных."
        except IntegrityError:
            await session.rollback()
            return "Ошибка: Пользователь с таким ID уже существует."


async def get_user_by_id(user_id: int) -> User | None:
    """
    Fetch a user from the database by their ID.

    Args:
        user_id (int): The ID of the user to fetch.
    Returns:
        User | None: The user object if found, otherwise None.
    """
    async with AsyncSessionLocal() as session:
        query_result = await session.execute(select(User).where(User.id == user_id))  # noqa: WPS221
        user = query_result.scalar_one_or_none()
        return user


async def add_task(user_id: int, name: str, tags: Optional[Tuple[str, ...]] = None) -> str:
    """
    Asynchronously adds a new task to the database for a specific user.

    Args:
        user_id (int): The ID of the user to whom the task belongs.
        name (str): The name of the task.
        tags (list[str], optional): List of tag names to associate with the task. Defaults to [].

    Returns:
        str: A message indicating the result of the operation.
    """
    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(user_id)
        if not user:
            return f"User with ID {user_id} does not exist."

        new_task = Task(name=name, user_id=user_id, is_completed=False)

        if tags:
            existing_tags = await session.execute(select(Tag).where(Tag.name.in_(tags)))  # noqa: WPS221
            existing_tags = existing_tags.scalars().all()

            new_tag_names = set(tags) - {str(tag.name) for tag in existing_tags}
            new_tags = [Tag(name=tag_name) for tag_name in new_tag_names]

            session.add_all(new_tags)
            await session.commit()

            new_task.tags.extend(existing_tags)
            new_task.tags.extend(new_tags)

        session.add(new_task)
        try:
            await session.commit()
            return f"Task with description '{name}' successfully added for user {user.name}."
        except IntegrityError:
            await session.rollback()
            return "Error: There was a problem adding the task."


async def get_tasks_by_user_id(user_id: int) -> list[Task]:
    """
    Asynchronously retrieves all tasks for a specific user from the database.

    Args:
        user_id (int): The ID of the user whose tasks are to be retrieved.

    Returns:
        list[Task]: A list of Task objects associated with the given user, or an empty list if no tasks are found.
    """
    async with AsyncSessionLocal() as session:

        query_result = await session.execute(
            select(Task).options(joinedload(Task.tags)).where(Task.user_id == user_id),
        )
        tasks = query_result.unique().scalars().all()
        return list(tasks)


async def get_not_completed_tasks_by_user_id(user_id: int) -> list[Task]:
    """
    Asynchronously retrieves all not completed tasks for a specific user from the database.

    Args:
        user_id (int): The ID of the user whose tasks are to be retrieved.

    Returns:
        list[Task]: A list of Task objects associated with the given user, or an empty list if no tasks are found.
    """
    async with AsyncSessionLocal() as session:

        # Pylance complains about using "== Bool", not "is Bool", but here this is correct.
        query_result = await session.execute(
            select(Task).options(joinedload(Task.tags)).where(Task.user_id == user_id, Task.is_completed == False),  # noqa: E712, E501
        )
        tasks = query_result.unique().scalars().all()
        return list(tasks)


async def mark_task_completed(task_id: int) -> str:
    """
    Asynchronously marks a task as completed by updating the `is_completed` field.

    Args:
        task_id (int): The ID of the task to mark as completed.

    Returns:
        str: A message indicating the result of the operation.
    """
    async with AsyncSessionLocal() as session:
        task = await session.get(Task, task_id)

        if not task:
            return f"Task with ID {task_id} does not exist."

        # Pylance complains about converting Literal[True] to Column[Bool], but this is correct.
        task.is_completed = True  # type: ignore

        try:
            await session.commit()  # Применяем изменения
            return f"Task with ID {task_id} has been marked as completed."
        except IntegrityError:
            await session.rollback()
            return "Error: There was a problem marking the task as completed."


async def search_tasks(
    user_id: int,
    query: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
) -> list[Task]:
    """
    Search for tasks based on user ID, query words, and tags.

    Args:
        user_id (int): The ID of the user whose tasks are being searched.
        query (Optional[list[str]], optional): A list of query words to search for in task names. Defaults to None.
        tags (Optional[list[str]], optional): A list of tags to filter tasks by. Defaults to None.
    Returns:
        list[Task]: A list of tasks that match the search criteria.
    Raises:
        ValueError: If neither 'query' nor 'tags' are provided.
    """
    if not query and not tags:
        raise ValueError("At least one of 'query' or 'tags' must be provided.")
    async with AsyncSessionLocal() as session:
        base_query = select(Task).options(joinedload(Task.tags)).where(Task.user_id == user_id)  # noqa: WPS221

        conditions = []
        if query:
            for query_word in query:
                conditions.append(or_(Task.name.ilike(f"%{query_word}%")))

        if tags:
            tag_conditions = [
                Task.tags.any(Tag.name == tag) for tag in tags
            ]
            conditions.append(or_(*tag_conditions))
        if conditions:
            base_query = base_query.where(or_(*conditions))

        query_result = await session.execute(base_query)
        tasks = query_result.unique().scalars().all()

        return list(tasks)


async def init_db() -> None:
    """
    Initialize the database by creating all tables defined in the metadata.

    This function asynchronously connects to the database engine, creates all
    tables defined in the Base metadata, and then disposes of the engine.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
