# src/api/main.py (дополнение; строку app = FastAPI() из урока заменяем на вариант с lifespan)
import asyncio
import json
from contextlib import asynccontextmanager

import aiohttp
import asyncpg
import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException

# from src.database.connection import DB_CONFIG

REVIEWS_URL = "https://api.reviews.sfmshop.ru/product"
resources: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Пул, клиент Redis и HTTP-сессия живут столько же, сколько приложение"""
    resources["pool"] = await asyncpg.create_pool(**DB_CONFIG, min_size=1, max_size=5)
    resources["redis"] = aioredis.from_url("redis://localhost:6379", decode_responses=True)
    resources["http"] = aiohttp.ClientSession()
    yield
    await resources["http"].close()
    await resources["redis"].aclose()
    await resources["pool"].close()


app = FastAPI(lifespan=lifespan)


@app.get("/products/{product_id}/full")
async def get_product_full(product_id: int):
    """Товар, отзывы и просмотры - три источника параллельно"""

    async def fetch_product():
        """Товар из PostgreSQL через репозиторий урока"""
        repository = ProductRepository(resources["pool"])
        return await repository.get_by_id(product_id)

    async def fetch_reviews():
        """Отзывы: сначала кэш Redis, при промахе - внешний API"""
        cache_key = f"cache:reviews:{product_id}"
        cached = await resources["redis"].get(cache_key)
        if cached:
            return json.loads(cached)

        try:
            async with resources["http"].get(
                f"{REVIEWS_URL}/{product_id}",
                timeout=aiohttp.ClientTimeout(total=3),
                ) as response:
                response.raise_for_status()
                reviews = await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return []

        await resources["redis"].setex(cache_key, 600, json.dumps(reviews))
        return reviews

    async def count_view():
        """Атомарный инкремент просмотров в Redis"""
        return await resources["redis"].incr(f"views:product:{product_id}")

    product, reviews, views = await asyncio.gather(
        fetch_product(),
        fetch_reviews(),
        count_view(),
        )

    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    return {
        **product,
        "price": float(product["price"]),
        "reviews": reviews,
        "views": views,
        }

async def fetch_data_async(session, url: str):
    try:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None

async def fetch_multiple_urls_async(urls: list):
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [fetch_data_async(session, url) for url in urls]   # создание списка задач
        return await asyncio.gather(*tasks)


result = asyncio.run(fetch_data_async("http://127.0.0.1:8000/products/1212g1"))
print(result)
