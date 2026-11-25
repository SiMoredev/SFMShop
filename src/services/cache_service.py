import asyncio
import json
from redis.exceptions import RedisError
import redis.asyncio as redis
import logging
import functools
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff


redis_client = redis.Redis(
    host="localhost", 
    port=6379, 
    db=0, 
    decode_responses=True,
    socket_connect_timeout=0.5,
    socket_timeout=0.5, 
    retry=Retry(NoBackoff(), 0)
    )
logger = logging.getLogger(__name__)

def safe_cache(func):
    """Если Redis недоступен — пишем предупреждение в лог и возвращаем None вместо ошибки."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except RedisError as e:
            logger.warning("Redis недоступен в %s: %s", func.__name__, e)
            return None
    return wrapper

class CacheService:
    """Обёртка над Redis: только get/set/delete, без обращений к БД."""

    def __init__(self, redis_client: redis.Redis = redis_client):
        self.redis_client = redis_client

    # --- ключи в одном месте, чтобы не было опечаток ---
    @staticmethod
    def _product_key(product_id: int) -> str:
        return f"product:{product_id}"

    @staticmethod
    def _page_key(limit: int, offset: int) -> str:
        return f"products:page:{limit}:{offset}"

    # --- товары ---
    @safe_cache
    async def set_product(self, product_id: int, product: dict, ttl: int = 3600) -> None:
        await self.redis_client.set(self._product_key(product_id), json.dumps(product), ex=ttl)

    @safe_cache
    async def get_product_by_id(self, product_id: int) -> dict | None:
        cached = await self.redis_client.get(self._product_key(product_id))
        return json.loads(cached) if cached is not None else None

    @safe_cache
    async def set_products(self, products: list, limit: int, offset: int, ttl: int = 3600) -> None:
        await self.redis_client.set(self._page_key(limit, offset), json.dumps(products), ex=ttl)

    @safe_cache
    async def get_products_page(self, limit: int, offset: int) -> list | None:
        cached = await self.redis_client.get(self._page_key(limit, offset))
        return json.loads(cached) if cached is not None else None

    @safe_cache
    async def invalidate_product_cache(self, product_id: int) -> None:
        await self.redis_client.delete(self._product_key(product_id))

    @safe_cache
    async def invalidate_products_cache(self) -> None:
        async for key in self.redis_client.scan_iter("products:page:*"):
            await self.redis_client.delete(key)


async def main():
    cache = CacheService()
    print("Товар:", await cache.get_product_by_id(1))


if __name__ == "__main__":
    asyncio.run(main())