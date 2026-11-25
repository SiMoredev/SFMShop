from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Product


class ProductRepository:
    """Репозиторий для работы с товарами."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, product_id: int) -> Product | None:
        """Получить товар по ID."""
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
            )
        return result.scalar_one_or_none()

    async def get_list(
        self,
        skip: int = 0,
        limit: int = 100,
        ) -> list[Product]:
        """Получить список товаров с пагинацией."""
        result = await self.session.execute(
            select(Product).offset(skip).limit(limit)
            )
        return list(result.scalars().all())

    async def create(self, product: Product) -> Product:
        """Создать новый товар."""
        self.session.add(product)
        await self.session.flush()
        return product

    async def update_stock(
        self,
        product_id: int,
        quantity_delta: int,
        ) -> None:
        """Обновить остаток товара."""
        product = await self.get_by_id(product_id)
        if product is None:
            raise ValueError(f"Товар {product_id} не найден")
        product.stock += quantity_delta

    async def search(
        self,
        name_query: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        ) -> list[Product]:
        """Поиск товаров по подстроке названия и диапазону цены."""
        query = select(Product)
        if name_query:
            query = query.where(Product.name.ilike(f"%{name_query}%"))
        if min_price is not None:
            query = query.where(Product.price >= min_price)
        if max_price is not None:
            query = query.where(Product.price <= max_price)
        result = await self.session.execute(query)
        return list(result.scalars().all())