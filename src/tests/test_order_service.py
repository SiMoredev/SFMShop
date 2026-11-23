# Пример: tests/test_order_service.py
from unittest.mock import Mock
from src.services.order_service import OrderService
from decimal import Decimal
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository

def test_bulk_discount():
    """Скидка 10% при заказе от 10 штук."""
    service = OrderService(
        order_repo=Mock(spec=OrderRepository), # Для _calculate_total не нужен
        product_repo=Mock(spec=ProductRepository),
        )
    assert service._calculate_total(price=Decimal("1000"), quantity=12) == 10800.0


def test_no_discount_below_threshold():
    """Без скидки при заказе менее 10 штук."""
    service = OrderService(
        order_repo=Mock(spec=OrderRepository),
        product_repo=Mock(spec=ProductRepository),
        )
    assert service._calculate_total(price=Decimal("1000"), quantity=9) == 9000.0