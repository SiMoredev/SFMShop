from datetime import datetime
import json
import secrets
from typing import Optional
from src.database.connection import redis_client, get_product_by_id, get_all_products, connect_to_db

class CacheService:
    def __init__(self, redis_client=redis_client):
        self.redis_client = redis_client

    def set_product(self, product_id: int, product: dict, ttl: int = 3600):
        """Сохранить товар в кэш"""
        self.redis_client.setex(
            f"product:{product_id}",
            ttl,
            json.dumps(product)
            )

    def set_products(self, products: list, ttl: int = 3600):
        """Сохранить список товаров в кэш"""
        self.redis_client.setex(
            "products:all",
            ttl,
            json.dumps(products)
            )
        
    def get_product_by_id(self, product_id):
        """Получение товара из кеша"""
        cache_key = f"products:{product_id}"
        cached = self.redis_client.get(cache_key)
        return json.loads(cached) if cached else None

    def get_products_page(self, limit: int, offset: int) -> Optional[dict]:
        cached = self.redis_client.get(f"products:{limit}:{offset}")
        return json.loads(cached) if cached else None


    def invalidate_products_cache(self):
        """Инвалидация кэша товаров"""
        self.redis_client.delete("products:all")


    def invalidate_product_cache(self, product_id):
        """Инвалидация кэша товара"""
        self.redis_client.delete(f"product:{product_id}")


    def create_user_session(self, user_id):

        session_token = secrets.token_urlsafe(32)
        session_key = f"session:{session_token}"
        session_data = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
            }

        self.redis_client.setex(session_key, 86400, json.dumps(session_data))
        return session_token

    
    def get_user_session(self, session_token) -> Optional[dict]:

        session_key = f"session:{session_token}"
        cashed = self.redis_client.get(session_key)
        if cashed is None:
            return None

        return json.loads(cashed)


    def delete_user_session(self, session_token):

        session_key = f"session:{session_token}"
        self.redis_client.delete(session_key)


# Тестирование
if __name__ == "__main__":

    cache = CacheService()
    # Тест кэширования товара
    product = cache.get_product_by_id(1)
    print(f"Товар: {product}")
    
    # Тест сессий
    session_token = cache.create_user_session(user_id=1)
    print(f"Сессия создана: {session_token}")
    
    session = cache.get_user_session(session_token)
    print(f"Сессия: {session}")