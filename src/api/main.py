# Файл src/api/main.py
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from src.models.exceptions import ValidationEmailError
from fastapi.testclient import TestClient
from src.database.connection import (
    connect_to_db, 
    add_product,
    get_product_by_id, 
    count_products, 
    get_products_page,
    update_product_db,
    delete_product_db,
    get_users, 
    get_user_by_id,
    create_user,
    create_order,
    )
from src.schemas.schemas import ProductCreate, ProductUpdate, OrderCreate, UserCreate
from src.models.product import Product
from src.models.metaclasses import ModelRegistryMeta


@asynccontextmanager
async def lifespan(app: FastAPI):
    global conn
    conn = connect_to_db()
    yield
    if conn:
        conn.close()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Внутренняя ошибка сервера: {str(exc)}"}
    )


@app.post("/products", status_code=status.HTTP_201_CREATED)
def add_product_endpoint(product: ProductCreate):
    new_product = add_product(conn, product.name, product.price, product.quantity)
    return new_product


@app.get("/products")
def get_products(limit: int = 10, offset: int = 0):
    total = count_products(conn)
    rows = get_products_page(conn, limit, offset)
    products = []
    if rows:
        for row in rows:
            product = Product(row[1], row[2], row[3])
            product.id = row[0]
            products.append(product.__dict__)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Товары не найдены"
            )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "products": products
    }


@app.get("/products/{product_id}")
def get_product(product_id: int):
    """Получить товар по ID"""
    product = get_product_by_id(conn, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Товар с id={product_id} не найден"
        )
    return product


@app.put("/products/{product_id}")
def update_product(product_id: int, product_data: ProductUpdate):
    if get_product_by_id(conn, product_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Товар не найден"
            )
    update_product_db(conn, product_id, product_data.name, product_data.price, product_data.quantity)
    return {"id": product_id, "message": "Товар обновлен"}


@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    deleted = delete_product_db(conn, product_id)
    if deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Товар не найден"
            )
    return {"message": "Товар удален"}


@app.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order_endpoint(order: OrderCreate):
    """Создать новый заказ"""
    user = get_user_by_id(conn, order.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с id={order.user_id} не найден"
        )
    row = get_product_by_id(conn, order.product_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Товар с id={order.product_id} не найден"
        )
    new_product = Product(row[0], row[1], row[2])
    total = new_product.get_total_price()
    new_order = create_order(conn, order.user_id, total)
    order_obj = []
    order_obj.append(order)
    return {"message": "Заказ создан", "order": new_order}

    
@app.get("/users")
def get_users_endpoint(limit: int = 10, offset: int = 0):
    """Получить список пользователей"""
    users = get_users(conn, limit, offset)
    return users


@app.get("/users/{user_id}")
def get_user(user_id: int):
    """Получить пользователя по ID"""
    user = get_user_by_id(conn, user_id)
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
        new_user = create_user(conn, user.name, user.email)
    except ValidationEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return new_user
    
def test_api():
    client = TestClient(app)

    # Тест POST /products
    response = client.post("/products", json={"name": "Sweets", "price": 1000, "quantity": 55})
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
    response = client.put("/products/1", json={"name": "Bread", "price": 100, "quantity": 10})
    assert response.status_code == 200
    print("PUT /products/1: OK")

    # Тест DELETE /products/{id}
    response = client.delete(f"/products/{new_id}")
    assert response.status_code == 200
    print(f"DELETE /products/{new_id}: OK")

    # Тест POST /orders
    response = client.post("/orders", json={"user_id": 1, "product_id": 2, "quantity": 1})
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
    conn = connect_to_db()
    test_api()
    print("Зарегистрированные классы:")
    for name, cls in ModelRegistryMeta._registry.items():
        print(f"  {name}: {cls}")
    print(ModelRegistryMeta._registry)
