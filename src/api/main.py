# Файл src/api/main.py
from fastapi import FastAPI, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from src.api.models.exceptions import ValidationEmailError
from fastapi.testclient import TestClient
from src.database.queries_orm import (
    get_products_page, get_product_by_id, 
    update_product, add_product, delete_product,
    get_user_by_id, get_users, create_user, create_order,
    get_order
)
from src.schemas.schemas import ProductCreate, ProductUpdate, OrderCreate, UserCreate
from src.api.models.metaclasses import ModelRegistryMeta
from src.services.async_service import process_orders_async
from src.services.cache_service import CacheService
from src.services.log_service import save_log, init_logs_indexes
import traceback
import logging
from starlette.concurrency import run_in_threadpool
from contextlib import asynccontextmanager
import asyncpg
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
db_pool: asyncpg.Pool | None = None
http_client: httpx.AsyncClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_in_threadpool(init_logs_indexes)
    global db_pool, http_client

    # Создание пула БД и HTTP-клиента при старте
    db_pool = await asyncpg.create_pool(
        (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        ),
        min_size=10,
        max_size=20,
        command_timeout=10
        )
    http_client = httpx.AsyncClient(timeout=5.0)

    # Корректное завершение
    await http_client.aclose()
    await db_pool.close()
    yield

app = FastAPI(lifespan=lifespan)
cache_service = CacheService()


resources: dict = {}


@app.post("/orders/process")
async def process_orders_endpoint(order_ids: list[int], background_tasks: BackgroundTasks):
    """Endpoint для обработки заказов"""
    try:
        # Асинхронная обработка заказов
        results = await process_orders_async(order_ids)
        return {
            "status": "success",
            "processed": len(results),
            "results": results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/orders/process-background")
async def process_orders_background(order_ids: list[int], background_tasks: BackgroundTasks):
    """Endpoint для фоновой обработки заказов"""
    background_tasks.add_task(process_orders_async, order_ids)
    return {
        "status": "accepted",
        "message": "Обработка заказов запущена в фоне"
    }


@app.get("/products/{product_id}/full")
async def get_product_full(product_id: int):
    """Товар, отзывы и просмотры - три источника параллельно"""
    # Твой код здесь
    pass


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    try:
        await run_in_threadpool(save_log, {
            "type": "error",
            "method": request.method,
            "endpoint": request.url.path,
            "status_code": 500,
            "message": str(exc),
            "error_type": type(exc).__name__,
            "traceback": "".join(traceback.format_exception(exc)),
        })
    except Exception:
        logger.exception("Не удалось записать ошибку в MongoDB")

    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"},
    )


@app.post("/products", status_code=status.HTTP_201_CREATED)
def add_product_endpoint(product: ProductCreate, background_tasks: BackgroundTasks):
    new_product = add_product(product.name, product.price, product.stock)
    background_tasks.add_task(save_log, {
        "type": "event",
        "event": "product_created",
        "product_id": new_product,
        "price": float(product.price),
        "stock": product.stock
    })
    return new_product


@app.get("/products")
def get_products_endpoint(limit: int = 10, offset: int = 0):
    """Получить список товаров с кэшированием"""
    # Проверка кэша
    cached_products = cache_service.get_products_page(limit, offset)
    if cached_products:
        return cached_products

    # Запрос к БД
    products_data = get_products_page(limit, offset)
    if products_data:
        cache_service.set_products(products_data, limit=limit, offset=offset)
        return products_data
    else:
        return []


@app.get("/products/{product_id}")
def get_product_endpoint(product_id: int):
    """Получить товар по ID"""
    cached_product = cache_service.get_product_by_id(product_id)
    if cached_product:
        return cached_product
    
    product = get_product_by_id(product_id)
    if product:
        cache_service.set_product(product_id, product)
        return product
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Товар с id={product_id} не найден"
        )


@app.put("/products/{product_id}")
def update_product_endpoint(product_id: int, product_data: ProductUpdate):
    if get_product_by_id(product_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Товар не найден"
            )
    update_product(product_id, product_data.name, product_data.price, product_data.stock)
    return {"id": product_id, "message": "Товар обновлен"}


@app.delete("/products/{product_id}")
def delete_product_endpoint(product_id: int):
    deleted = delete_product(product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Товар не найден"
            )
    return {"message": "Товар удален"}


@app.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order_endpoint(order: OrderCreate):
    """Создать новый заказ"""
    try:
        new_order = create_order(order.user_id, order.product_id, order.quantity)
        return {"message": "Заказ создан", "order": new_order}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/orders/{order_id}")
def get_order_endpoint(order_id: int):
    order = get_order(order_id)
    return order

    
@app.get("/users")
def get_users_endpoint(limit: int = 10, offset: int = 0):
    """Получить список пользователей"""
    users = get_users(limit, offset)
    return users


@app.get("/users/{user_id}")
def get_user_endpoint(user_id: int):
    """Получить пользователя по ID"""
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с id={user_id} не найден"
        )
    return user


@app.post("/users", status_code=status.HTTP_201_CREATED)
def create_user_endpoint(user: UserCreate):
    """Создать нового пользователя"""
    try:
        new_user = create_user(user.name, user.email)
        save_log({
            "title": "create_user",
            "user": user.name,
            "email": user.email
            })
    except ValidationEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return new_user
    
def test_api():
    client = TestClient(app)

    # Тест POST /products
    response = client.post("/products", json={"name": "Sweets", "price": 1000, "stock": 55})
    assert response.status_code == 201
    print(response.json())
    new_id = response.json()["id"]
    print("POST /products: OK")

    # Тест GET /products
    response = client.get("/products")
    assert response.status_code == 200
    print("GET /products: OK")

    # Тест GET /products/{id}
    response = client.get("/products/1")
    assert response.status_code == 200
    print("GET /products/1: OK")

    # Тест PUT /products/{id}
    response = client.put("/products/1", json={"name": "Bread", "price": 100, "stock": 10})
    assert response.status_code == 200
    print("PUT /products/1: OK")

    # Тест DELETE /products/{id}
    response = client.delete(f"/products/{new_id}")
    assert response.status_code == 200
    print(f"DELETE /products/{new_id}: OK")

    # Тест POST /orders
    response = client.post("/orders", json={"user_id": 1, "product_id": 2, "stock": 1})
    assert response.status_code == 201
    print("POST /orders: OK")

    # Тест GET /users
    response = client.get("/users")
    assert response.status_code == 200
    print("GET /users: OK")

    # Тест GET /users/1
    response = client.get("/users/1")
    assert response.status_code == 200
    print("GET /users/1: OK")

    # Тест POST /users
    response = client.post("/users", json={"name": "Andrey", "email": "andrey@yandex.ru"})
    assert response.status_code == 201
    print("POST /users: OK")

if __name__ == "__main__": 
    test_api()
    print("Зарегистрированные классы:")
    for name, cls in ModelRegistryMeta._registry.items():
        print(f"  {name}: {cls}")
    print(ModelRegistryMeta._registry)
