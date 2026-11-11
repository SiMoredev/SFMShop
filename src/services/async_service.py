# Файл src/services/async_service.py
import asyncio
import aiohttp
import time
import asyncio
import time
from src.database.models import Order
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from src.database.queries_orm import process_order as process_order_orm


load_dotenv()


engine = create_async_engine(
    f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def fetch_url_async(url: str):
    """Асинхронный запрос к URL"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    except Exception as e:
        print(f"Ошибка при запросе к {url}: {e}")
        return None


async def fetch_with_session(session: aiohttp.ClientSession, url: str):
    """Один запрос в уже открытой сессии"""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None
    except aiohttp.ClientError as error:
        print(f"Ошибка при запросе к {url}: {error}")
        return None


async def fetch_multiple_urls_async(urls: list):
    """Параллельные запросы к нескольким URL"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_with_session(session, url) for url in urls]
        return await asyncio.gather(*tasks)


async def compare_parallel_and_sequential(urls: list):
    """Замер: параллельный проход против последовательного по тем же URL"""
    start = time.perf_counter()
    results = await fetch_multiple_urls_async(urls)
    parallel_time = time.perf_counter() - start

    start = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        for url in urls:
            await fetch_with_session(session, url)
    sequential_time = time.perf_counter() - start

    print(f"Параллельно: {parallel_time:.2f} секунд")
    print(f"Последовательно: {sequential_time:.2f} секунд")
    if parallel_time > 0:
        print(f"Ускорение: в {sequential_time / parallel_time:.1f} раз")
    return results


async def process_order(order_id: int):
    """Получить заказ, проверить и перевести в статус processing"""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. Получение заказа
            stmt = (
                select(Order)
                .options(selectinload(Order.order_items))
                .where(Order.id == order_id)
                .with_for_update()
            )
            order = (await session.execute(stmt)).scalar_one_or_none()

            # 2. Валидация
            if order is None:
                return f"Заказ {order_id}: не найден"
            if order.status != "pending":
                return f"Заказ {order_id}: уже в статусе {order.status}"
            if not order.order_items:
                return f"Заказ {order_id}: нет позиций"

            items_total = sum(item.price * item.quantity for item in order.order_items)
            if items_total != order.total:
                order.status = "error"
                return f"Заказ {order_id}: сумма не совпадает ({order.total} != {items_total})"

            # 3. Обновление статуса
            order.status = "processing"

    return f"Заказ {order_id} обработан"


async def process_orders_async(order_ids: list):
    """Параллельная обработка списка заказов"""
    tasks = [process_order(order_id) for order_id in order_ids]
    results = await asyncio.gather(*tasks)
    return results


async def reset_statuses(order_ids):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(
                update(Order).where(Order.id.in_(order_ids)).values(status="pending")
            )


async def fetch_order_details_async(order_id: int):
    """Получить дополнительные данные о заказе из внешнего API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://127.0.0.1:8000/orders/{order_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    except Exception as e:
        print(f"Ошибка при запросе данных для заказа {order_id}: {e}")
        return None


# Тест
async def main():

    order_ids = list(range(1, 101))  # 100 заказов
    await reset_statuses(order_ids) 
    # Асинхронная обработка
    start = time.perf_counter()
    results = await process_orders_async(order_ids)
    end = time.perf_counter()
    print(f"Асинхронная обработка: {end - start} секунд")
    
    # Сравнение с синхронной версией (для демонстрации)
    await reset_statuses(order_ids)
    start = time.perf_counter()
    for order in range(1,101):
        process_order_orm(order)
    end = time.perf_counter()
    print(f"Синхронная обработка: {end - start} секунд")
    await engine.dispose()


# Асинхронная обработка: 5.127826749987435 секунд
# Синхронная обработка: 10.193312124989461 секунд


if __name__ == "__main__":
    asyncio.run(main())

