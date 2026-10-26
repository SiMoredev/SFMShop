from datetime import datetime
import json
import secrets
from src.database.connection import redis_client, get_product_by_id, get_all_products, connect_to_db


def get_cached_products():
    """Получение товаров с кэшированием"""
    cache_key = "products:all"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    products = get_all_products(connect_to_db())
    redis_client.setex(cache_key, 3600, json.dumps(products))
    return products


def get_cached_product(product_id):

    cashe_key = f"product:{product_id}"

    cashed = redis_client.get(cashe_key)
    if cashed:
        return json.loads(cashed)
    
    product = get_product_by_id(connect_to_db(), product_id)

    redis_client.setex(cashe_key, 86400, json.dumps(product))

    return product

def invalidate_products_cache():
    """Инвалидация кэша товаров"""
    redis_client.delete("products:all")

def invalidate_product_cache(product_id):
    """Инвалидация кэша товара"""
    redis_client.delete(f"product:{product_id}")

def create_user_session(user_id):

    session_token = secrets.token_urlsafe(32)
    session_key = f"session:{session_token}"
    session_data = {
        "user_id": user_id,
        "created_at": datetime.now().isoformat()
        }

    redis_client.setex(session_key, 86400, json.dumps(session_data))
    return session_token
    
def get_user_session(session_token):

    session_key = f"session:{session_token}"
    cashed = redis_client.get(session_key)
    if cashed is None:
        return None

    return json.loads(cashed)

def delete_user_session(session_token):

    session_key = f"session:{session_token}"
    redis_client.delete(session_key)

# Тестирование
if __name__ == "__main__":
    # Тест кэширования товара
    product = get_cached_product(1)
    print(f"Товар: {product}")
    
    # Тест сессий
    session_token = create_user_session(user_id=1)
    print(f"Сессия создана: {session_token}")
    
    session = get_user_session(session_token)
    print(f"Сессия: {session}")
