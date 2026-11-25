from decimal import Decimal
from src.core.order_status import change_status
from src.repositories.order_repository import OrderRepository
from src.repositories.user_repository import UserRepository
from src.core.exceptions import InsufficientFundsError
from src.database.models import Order

class PaymentService:

    def __init__(self, order_repo: OrderRepository, user_repo: UserRepository) -> None:
        self.order_repo = order_repo
        self.user_repo = user_repo

    async def pay_order(self, order_id: int, user_id: int) -> Order:
        """Оплатить заказ processing -> paid"""
        order = await self.order_repo.get_by_id(order_id, for_update=True)
        if order is None or order.user_id != user_id:
            raise ValueError(f"Заказ {order_id} не найден")
        user = await self.user_repo.get_by_id(order.user_id, for_update=True)
        if user is None:
            raise ValueError(f"Пользователь {order.user_id} не существует")
        if user.balance < order.total:
            raise InsufficientFundsError(f"На балансе {user.balance}, нужно {order.total}")
        change_status(order, "paid") # бросит InvalidOrderError, если не processing
        user.balance -= order.total
        return order
                