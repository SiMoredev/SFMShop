from src.models.order import Order, OrderValidator
from typing import Optional

class OrderFactory:
    """Фабрика для создания заказов"""
    @staticmethod
    def create_order(user, products, order_id: Optional[int] = None):
        order = Order(user, *products, order_id=order_id)
        OrderValidator.validate(order)
        return order
    
    @classmethod
    def create_order_from_dict(cls, data):
        """Создание заказа из словаря"""
        return cls.create_order(
            data["order_id"],
            data["items"],
            data["user"]
        )