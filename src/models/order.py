from src.models.mixins import LoggableMixin
from typing import Optional
from src.models.metaclasses import ModelRegistryMeta
from src.models.product import Product
from src.models.user import User
from decimal import Decimal


class Order(LoggableMixin, metaclass=ModelRegistryMeta):

    def __init__(self, user, *products: Product, order_id: Optional[int] = None):
        self.user = user
        self.products = list(products)
        self.order_id = order_id
        user_name = user.name if hasattr(user, "name") else str(user)
        self.log(f"Создан заказ для {user_name}")

    def __len__(self):
        return len(self.products)

    def __contains__(self, item):
        if isinstance(item, str):
            return any(p.name == item for p in self.products)
        return item in self.products

    def __add__(self, other):
        if not self.user == other.user:
            raise ValueError("Пользователи должны совпадать для объединения заказа")
        new_products = self.products + other.products
        return Order(self.user, *new_products, order_id=None)

    def __str__(self):
        products_str = "; ".join(str(p) for p in self.products)
        return f"Заказ на имя {self.user}, Товары: {products_str}"

    def __lt__(self, other):
        return self.order_id < other.order_id
    
    def add_product(self, product: Product):
        if product in self.products:
            raise KeyError("Товар уже находится в корзине")
        self.products.append(product)

    def to_dict(self) -> dict:
        return {
            "user": self.user.to_dict() if hasattr(self.user, "to_dict") else str(self.user),
            "products": [p.to_dict() for p in self.products],  # ← рекурсивный вызов
            "order_id": self.order_id,
        }


    """
    Обертка ниже для того, чтобы остальной код продолжал работать,
    по сути это перенаправление метода на новый класс.
    используют при рефакторинге и разделения ответственности старого функционала
    на отдельные подклассы для соблюдения принципа SOLID
    """
    def calculate_total(self):
        return OrderCalculator.calculate_total(self)


class OrderCalculator:

    @staticmethod
    def calculate_total(order: Order) -> Decimal:
        total = Decimal("0")
        for product in order.products:
            total = total + product.get_total_price
        return total

    @staticmethod
    def calculate_discount(order: Order, discount_percent: float) -> Decimal:
        """Рассчитать стоимость со скидкой"""
        total = OrderCalculator.calculate_total(order)
        return total * (Decimal("1") - Decimal(str(discount_percent)) / Decimal("100"))


class OrderValidator:

    @staticmethod
    def validate(order: Order) -> bool:
        if not order.products:
            raise ValueError("Заказ не может быть пустым")
        if not order.user:
            raise ValueError("Заказ должен иметь пользователя")
        for product in order.products:
            if not isinstance(product, Product):
                raise TypeError(f"Товар {product} должен быть типа Product")
        if not isinstance(order.user, User):
            raise TypeError("Пользователь должен быть типа User")
        return True


def main():

    product1 = [
        Product("Ноутбук", Decimal("100000"), 10),
        Product("Мышь", Decimal("500"), 5)
    ]

    product2 = Product("Клавиатура", Decimal("2000"), 5)
    product3 = Product("Монитор", Decimal("10000"), 2)

    order1 = Order("Sergey", *product1, order_id=2)
    order2 = Order("Sergey", product2, order_id=3)
    print(order1)

    print(len(order1))  # 2
    print("Ноутбук" in order1)  # True
    order3 = order1 + order2  # Объединение заказов
    order3.add_product(product3)
    print(order3)
    sorted_orders = sorted([order2, order1])  # Сортировка через __lt__

if __name__ == "__main__":
    main()