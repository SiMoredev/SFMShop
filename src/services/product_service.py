# Файл src/services/product_service.py
from src.schemas.product import ProductResponse
from src.repositories.product_repository import ProductRepository
from src.services.cache_service import CacheService


class ProductService:
    def __init__(self, product_repo: ProductRepository, cache: CacheService):
        self.product_repo = product_repo
        self.cache = cache

    async def get_product(self, product_id: int) -> dict | None:
        """Получить заказ по ID."""
        cached_product = await self.cache.get_product_by_id(product_id)
        if cached_product:
            return cached_product
        product = await self.product_repo.get_by_id(product_id)
        if product is None:
            return None
        
        data = ProductResponse.model_validate(product).model_dump(mode="json")
        await self.cache.set_product(product_id, data)
        return data

    async def get_products(self, skip: int, limit: int) -> list[dict]:
        """Список товаров: сначала Redis, при промахе — база и запись в Redis."""
        cached = await self.cache.get_products_page(limit=limit, offset=skip)
        if cached is not None:
            return cached

        products = await self.product_repo.get_list(skip=skip, limit=limit)
        data = [ProductResponse.model_validate(p).model_dump(mode="json") for p in products]
        await self.cache.set_products(data, limit=limit, offset=skip)
        return data

    async def search_products(
        self,
        name_query: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        ):

        return await self.product_repo.search(
            name_query=name_query,
            min_price=min_price,
            max_price=max_price
        )