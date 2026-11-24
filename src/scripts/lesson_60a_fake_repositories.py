# Файл scripts/lesson_60a_fake_repositories.py
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock

# Корень проекта в sys.path, чтобы импорт src.* работал при запуске файла напрямую
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class SimpleProduct:
    """Простая модель товара для тестирования."""

    def __init__(self, id, price, quantity):
        self.id = id
        self.price = price
        self.quantity = quantity

class FakeProductRepository:
    """Заглушка: возвращает заранее заданный товар."""

    def __init__(self, product):
        self.product = product
        self.stock_updates = []

    async def get_by_id(self, product_id):
        return self.product

    async def update_stock(self, product_id, delta):
        self.stock_updates.append((product_id, delta))
        self.product.quantity += delta


class FakeOrderRepository:
    """Заглушка: сохраняет заказы в список."""

    def __init__(self):
        self.saved_orders = []

    async def create(self, order):
        order.id = len(self.saved_orders) + 1
        self.saved_orders.append(order)
        return order


async def test_order_with_discount():
    """Проверяем скидку 10% при заказе от 10 штук."""
    product = SimpleProduct(id=1, price=1000.0, quantity=50)
    product_repo = FakeProductRepository(product)
    order_repo = FakeOrderRepository()

    from src.services.order_service import OrderService
    service = OrderService(
        order_repo=Mock(spec=order_repo),
        product_repo=Mock(spec=product_repo),
    )

    order = await service.create_order(
        user_id=1,
        product_id=1,
        quantity=10,
    )

    # 1000 * 10 * 0.9 = 9000
    assert order.total == 9000.0, f"Ожидали 9000, получили {order.total}"
    # Остатки списаны
    assert product_repo.stock_updates == [(1, -10)]
    print("Все проверки пройдены.")


async def test_insufficient_stock():
    """Проверяем ошибку при недостатке товара."""
    product = SimpleProduct(id=1, price=1000.0, quantity=3)
    product_repo = FakeProductRepository(product)
    order_repo = FakeOrderRepository()

    from src.services.order_service import OrderService, InsufficientStockError
    service = OrderService(
        order_repo=Mock(spec=order_repo),
        product_repo=Mock(spec=product_repo),
    )

    try:
        await service.create_order(
            user_id=1,
            product_id=1,
            quantity=10,
        )
    except InsufficientStockError as e:
        print(f"Ожидаемая ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(test_order_with_discount())
    asyncio.run(test_insufficient_stock())