from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Order


class OrderRepository:
    """Репозиторий для работы с заказами."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, order_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
            )
        return result.scalar_one_or_none()

    async def create(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.flush()
        return order