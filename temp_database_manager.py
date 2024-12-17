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
        """
        Asynchronously sets a temporary value for a user by name.

        Args:
            user_id (int): The ID of the user.
            temp_value_name (str): The name of the temporary value to set.
            temp_value (str): The value to set for the specified temporary value name.
        Returns:
            None
        """
        user_namespace = self._get_user_namespace(user_id)
        full_user_namespace = f"{user_namespace}:{temp_value_name}"
        await self._redis_client.set(full_user_namespace, temp_value, ex=self._ttl)

    async def get_user_temp_value_by_name(self, user_id: int, key: str) -> str:
        """
        Retrieve a temporary value for a user by key from the Redis database.

        Args:
            user_id (int): The ID of the user.
            key (str): The key associated with the temporary value.
        Returns:
            str: The temporary value associated with the given key for the specified user.
        Raises:
            ValueError: If the key does not exist for the specified user.
        """
        user_namespace = self._get_user_namespace(user_id)
        if not await self._redis_client.exists(f"{user_namespace}:{key}"):
            raise ValueError(f"Data with name {key} not found for user {user_id}")
        temp_value = await self._redis_client.get(f"{user_namespace}:{key}")
        return temp_value

    async def add_task_tag(self, user_id: int, tag: str) -> None:
        """
        Asynchronously adds a tag to the user's task tags list in the Redis database.

        Args:
            user_id (int): The ID of the user.
            tag (str): The tag to be added.
        Returns:
            None
        """
        user_namespace = self._get_user_namespace(user_id)
        task_tag_key = f"{user_namespace}:tags"
        # because the Redis object interface is both sync and async, but this instance is initialized as async.
        await self._redis_client.rpush(task_tag_key, tag)  # type: ignore

    async def get_task_tags(self, user_id: int) -> list:
        """
        Asynchronously retrieves the list of task tags for a given user.

        Args:
            user_id (int): The ID of the user whose task tags are to be retrieved.
        Returns:
            list: A list of task tags associated with the user.
        Raises:
            Any exceptions raised by the Redis client during the operation.
        """
        user_namespace = self._get_user_namespace(user_id)
        task_tag_key = f"{user_namespace}:tags"
        # because the Redis object interface is both sync and async, but this instance is initialized as async.
        tags = await self._redis_client.lrange(task_tag_key, 0, -1)  # type: ignore
        return list(tags)

    async def clear_user_data_from_redis(self, user_id: int) -> None:
        """
        Asynchronously clears all data associated with a specific user from Redis.

        Args:
            user_id (int): The ID of the user whose data is to be cleared.
        Returns:
            None
        """
        user_namespace = f"user:{user_id}"

        keys = await self._redis_client.keys(f"{user_namespace}:*")
        if keys:
            await self._redis_client.delete(*keys)

    def _get_user_namespace(self, user_id: int) -> str:
        return f"user:{user_id}"
