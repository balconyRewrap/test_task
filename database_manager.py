# TODO: ADD DOCSTRING
from decouple import config
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.future import select

from models import Base, User


def is_env_valid():  # noqa: C901, WPS231, WPS238
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
    if not isinstance(config("API_TOKEN"), str):
        raise ValueError("API_TOKEN isn't defined in .env")

    if not isinstance(config("REDIS_HOST"), str):
        raise ValueError("REDIS_HOST isn't defined in .env")

    if not isinstance(config("REDIS_PORT"), int):
        raise ValueError("REDIS_PORT isn't defined in .env")

    if not isinstance(config("MARIADB_HOST"), str):
        raise ValueError("MARIADB_HOST isn't defined in .env")

    if not isinstance(config("MARIADB_USER"), str):
        raise ValueError("MARIADB_USER isn't defined in .env")

    if not isinstance(config("MARIADB_PASSWORD"), str):
        raise ValueError("MARIADB_PASSWORD isn't defined in .env")

    if not isinstance(config("MARIADB_DATABASE"), str):
        raise ValueError("MARIADB_DATABASE isn't defined in .env")
    return True


MARIADB_USER = config("MARIADB_USER")
MARIADB_PASSWORD = config("MARIADB_PASSWORD")
MARIADB_HOST = config("MARIADB_HOST")
MARIADB_DATABASE = config("MARIADB_DATABASE")
DATABASE_URL = f"mariadb+asyncmy://{MARIADB_USER}:{MARIADB_PASSWORD}@{MARIADB_HOST}/{MARIADB_DATABASE}?charset=utf8mb4"  # noqa: WPS221

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


async def init_db() -> None:
    """
    Initialize the database by creating all tables defined in the metadata.

    This function asynchronously connects to the database engine, creates all
    tables defined in the Base metadata, and then disposes of the engine.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
