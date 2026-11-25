from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Order
from sqlalchemy.orm import selectinload


class OrderRepository:
    """Репозиторий для работы с заказами."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, order_id: int, for_update: bool = False) -> Order | None:
        
        query = select(Order).options(selectinload(Order.order_items)).where(Order.id == order_id)
        if for_update:
            query = query.with_for_update()
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.flush()
        return order