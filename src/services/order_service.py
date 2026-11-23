# Файл src/services/order_service.py
from decimal import Decimal

from src.database.models import Order
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.api.models.exceptions import InsufficientStockError


class OrderService:
    """Сервис для работы с заказами."""

    # Минимальное количество для оптовой скидки
    BULK_DISCOUNT_THRESHOLD = 10
    BULK_DISCOUNT_RATE = 0.9

    def __init__(
        self,
        order_repo: OrderRepository,
        product_repo: ProductRepository,
        ):
        self.order_repo = order_repo
        self.product_repo = product_repo

    async def create_order(
        self,
        user_id: int,
        product_id: int,
        quantity: int,
        ) -> Order:
        """Создать заказ с проверкой остатков и расчётом скидки."""
        product = await self.product_repo.get_by_id(product_id)
        if product is None:
            raise ValueError(f"Товар {product_id} не найден")

        if product.stock < quantity:
            raise InsufficientStockError(
                f"На складе {product.stock} шт., запрошено {quantity}"
                )

        total = self._calculate_total(product.price, quantity)

        order = Order(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            total=total,
            )
        order = await self.order_repo.create(order)

        # Списываем остатки
        await self.product_repo.update_stock(product_id, -quantity)

        return order

    def _calculate_total(self, price: Decimal, quantity: int) -> float:
        """Расчёт стоимости с учётом оптовой скидки."""
        # price из ORM-модели приходит как Decimal (Numeric) -- приводим к float
        total = float(price) * quantity
        if quantity >= self.BULK_DISCOUNT_THRESHOLD:
            total *= self.BULK_DISCOUNT_RATE
        return total

    async def cancel_order(self, order_id: int) -> Order:
        """Отменить заказ и вернуть товар на склад."""
        order = await self.order_repo.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Заказ {order_id} не найден")

        if order.status == "cancelled":
            raise ValueError("Заказ уже отменён")

        order.status = "cancelled"

        # Возвращаем товар на склад
        await self.product_repo.update_stock(
            order.product_id,
            order.quantity,
            )

        return order

    async def get_order(self, order_id: int) -> Order | None:
        """Получить заказ по ID (эндпоинт GET /orders/{order_id})."""
        return await self.order_repo.get_by_id(order_id)