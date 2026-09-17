from src.models.order_factory import OrderFactory
from src.models.payments import CardPayment
from src.models.delivery_strategy import StandardDelivery
from src.models.product import Product
from src.models.user import User
from decimal import Decimal


def process_advanced_order_system():
    """Демонстрация всех продвинутых концепций ООП"""

    # 5. Дескрипторы для валидации
    products = [
        Product("Ноутбук", Decimal("100000"), 10),
        Product("Клавиатура", Decimal("5000"), 10)  # Автоматическая валидация
    ]
    user = User("Sergey", "example@yandex.ru")
    
    # 1. Factory для создания заказов
    order = OrderFactory.create_order(user, *products, order_id=15)
    
    # 2. Strategy для расчета доставки
    delivery = StandardDelivery()
    delivery_cost = delivery.calculate_cost(5.0)
    
    # 3. Полиморфизм для платежей
    payment = CardPayment(1000)
    payment.process()
    
    # 4. Метакласс для сериализации
    order_json = order.to_dict()
    
    # 6. Миксины для логирования
    payment.log("Платеж обработан")
    
    # 7. Магические методы
    print(len(order))  # Количество товаров
    print("Ноутбук" in order)  # Проверка наличия
    
    response = {
        "order": order_json,
        "delivery_cost": delivery_cost,
        "total_price_order": order.calculate_total()
    }
    print(response)
    return response
if __name__ == "__main__":
    process_advanced_order_system()