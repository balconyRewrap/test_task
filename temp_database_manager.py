# TODO: ADD DOCSTRING
from decouple import config
from redis.asyncio.client import Redis


class TempDatabaseManager:
    # TODO: ADD DOCSTRING
    def __init__(self):
        """
        Initializes the TempDatabaseManager instance.

        Sets up a Redis client with the specified host and port from the configuration.
        The Redis client is configured to decode responses and use database 0.
        Also sets the default Time-To-Live (TTL) for the Redis entries.

        Attributes:
            _redis_client (Redis): The Redis client instance.
            _ttl (int): The default Time-To-Live (TTL) for the Redis entries, in seconds.
        """
        self._redis_client: Redis = Redis(
            host=config("REDIS_HOST"),  # type: ignore
            port=config("REDIS_PORT"),
            db=0,
            decode_responses=True,
        )
        # Time-To-Live
        self._ttl = 600

    async def set_user_temp_value_by_name(self, user_id: int, temp_value_name: str, temp_value: str) -> None:
        # TODO: ADD DOCSTRING
        user_namespace = self._get_user_namespace(user_id)
        full_user_namespace = f"{user_namespace}:{temp_value_name}"
        await self._redis_client.set(full_user_namespace, temp_value, ex=self._ttl)

    async def get_user_temp_value_by_name(self, user_id: int, key: str) -> str:
        # TODO: ADD DOCSTRING
        user_namespace = self._get_user_namespace(user_id)
        if not await self._redis_client.exists(f"{user_namespace}:{key}"):
            raise ValueError(f"Data with name {key} not found for user {user_id}")
        temp_value = await self._redis_client.get(f"{user_namespace}:{key}")
        return temp_value

    async def delete_user_temp_value_by_name(self, user_id: int, key: str) -> None:
        # TODO: ADD DOCSTRING
        user_namespace = self._get_user_namespace(user_id)
        await self._redis_client.delete(f"{user_namespace}:{key}")

    def _get_user_namespace(self, user_id: int) -> str:
        return f"user:{user_id}"
