import json
from typing import Any
from uuid import UUID

from redis.asyncio import Redis

from src.settings import get_settings

settings = get_settings()
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


class CacheClient:
    def __init__(self, client: Redis) -> None:
        self._client = client

    _VERSION_TTL_SECONDS: int = 86400  # 24 hours

    async def get_version(self, user_id: UUID, metric_id: UUID) -> int:
        key = f"records_ver:{user_id}:{metric_id}"
        value = await self._client.get(key)
        if value is None:
            await self._client.set(key, 1, ex=self._VERSION_TTL_SECONDS)
            return 1
        return int(value)

    async def bump_version(self, user_id: UUID, metric_id: UUID) -> None:
        key = f"records_ver:{user_id}:{metric_id}"
        pipe = self._client.pipeline()
        pipe.incr(key)
        pipe.expire(key, self._VERSION_TTL_SECONDS)
        await pipe.execute()

    async def get_json(self, key: str) -> Any | None:
        raw = await self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        await self._client.set(key, json.dumps(value), ex=ttl_seconds)


def get_cache_client() -> CacheClient:
    return CacheClient(redis_client)
