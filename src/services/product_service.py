# Файл src/services/product_service.py
from src.database.models import Product
from src.repositories.product_repository import ProductRepository


class ProductService:
    def __init__(self, product_repo: ProductRepository):
        self.product_repo = product_repo
        pass

    async def get_product(self, product_id: int) -> Product | None:
        """Получить заказ по ID (эндпоинт GET /orders/{order_id})."""
        return await self.product_repo.get_by_id(product_id)

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