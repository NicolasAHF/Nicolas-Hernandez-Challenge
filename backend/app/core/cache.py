import json
from typing import Protocol

import redis


def metrics_cache_key(plan_id: int) -> str:
    return f"plan:{plan_id}:metrics"


class Cache(Protocol):
    def get_json(self, key: str) -> dict | None: ...

    def set_json(self, key: str, value: dict, ttl: int) -> None: ...

    def delete(self, key: str) -> None: ...


class RedisCache:
    """Cache backed by Redis. Redis errors are swallowed so the application keeps
    working (and stays correct) when Redis is unavailable."""

    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    def get_json(self, key: str) -> dict | None:
        try:
            raw = self._client.get(key)
        except redis.RedisError:
            return None
        return json.loads(raw) if raw else None

    def set_json(self, key: str, value: dict, ttl: int) -> None:
        try:
            self._client.set(key, json.dumps(value), ex=ttl)
        except redis.RedisError:
            pass

    def delete(self, key: str) -> None:
        try:
            self._client.delete(key)
        except redis.RedisError:
            pass


class InMemoryCache:
    """In-process cache used in tests. No expiry — TTL is accepted and ignored."""

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def get_json(self, key: str) -> dict | None:
        return self._store.get(key)

    def set_json(self, key: str, value: dict, ttl: int) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)
