from decimal import ROUND_HALF_UP, Decimal
from src.database.models import Order, OrderItems
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.core.exceptions import InsufficientStockError, InvalidOrderError
from src.core.order_status import change_status


class OrderService:
    """Сервис для работы с заказами."""

    # Минимальное количество для оптовой скидки
    BULK_DISCOUNT_THRESHOLD = 10
    BULK_DISCOUNT_RATE = Decimal("0.9")

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
            total=total,
            order_items=[
                OrderItems(product_id=product_id, quantity=quantity, price=product.price),
            ],
            )
        order = await self.order_repo.create(order)

        # Списываем остатки
        await self.product_repo.update_stock(product_id, -quantity)

        return order

    def _calculate_total(self, price: Decimal, quantity: int) -> Decimal:
        """Расчёт стоимости с учётом оптовой скидки."""
        total = price * quantity
        if quantity >= self.BULK_DISCOUNT_THRESHOLD:
            total *= self.BULK_DISCOUNT_RATE
        return total.quantize(Decimal("0,01"), rounding=ROUND_HALF_UP)

    async def process_order(self, order_id: int, user_id: int) -> Order:
        """Проверить заказ и переверсти panding -> processing"""
        order = await self.order_repo.get_by_id(order_id, for_update=True)
        if order is None or order.user_id != user_id:
            raise ValueError(f"Заказ {order_id} не найден")
        if not order.order_items:
            raise InvalidOrderError(f"Заказ {order_id}: нет позиций")
        change_status(order, "processing")
        return order

    async def cancel_order(self, order_id: int, user_id: int) -> Order:
        """Отменить заказ и вернуть товар на склад."""
        order = await self.order_repo.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Заказ {order_id} не найден")
        if order.status == "cancelled":
            raise ValueError("Заказ уже отменён")
        change_status(order, "cancelled")
        for item in order.order_items:
            await self.product_repo.update_stock(item.product_id, item.quantity)
        return order

    async def get_order(self, order_id: int, user_id: int) -> Order | None:
        """Получить заказ по ID (эндпоинт GET /orders/{order_id})."""
        order = await self.order_repo.get_by_id(order_id)
        if order is None or order.user_id != user_id:
            return None
        return order
