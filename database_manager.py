# TODO: ADD DOCSTRING
from typing import Optional, Tuple

from decouple import config
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.future import select

from models import Base, Tag, Task, User


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
            select(Task).where(Task.user_id == user_id),
        )
        
        tasks = query_result.scalars().all()
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
