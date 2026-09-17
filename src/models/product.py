from src.models.exceptions import InsufficientStockError
from src.models.mixins import LoggableMixin, SerializableMixin
from src.models.metaclasses import ModelRegistryMeta
from src.models.descriptors import PositiveNumber, CachedProperty
from typing import Optional
from decimal import Decimal
from abc import ABC, abstractmethod


class DiscountStrategy(ABC):
    @abstractmethod
    def apply(self, price: Decimal) -> Decimal:
        pass


class FixedDiscount(DiscountStrategy):

    def __init__(self, fixed_discount: Decimal) -> None:
        self.fixed_discount = fixed_discount

    def apply(self, price: Decimal) -> Decimal:
        return max(Decimal("0"), price - self.fixed_discount)

class PersentDiscount(DiscountStrategy):

    def __init__(self, persent_discount) -> None:
        self.persent_discount = persent_discount

    def apply(self, price: Decimal) -> Decimal:
        return price * (1 - self.persent_discount / 100)


class Product(LoggableMixin, SerializableMixin, metaclass=ModelRegistryMeta):

    price = PositiveNumber[Decimal]("_price")
    quantity = PositiveNumber[int]("_quantity")

    def __init__(self, name: str, price: Decimal, quantity: int):
        self.name = name
        self.price = price
        self.quantity = quantity
        self.id: Optional[int] = None
        self.log(f"Создан товар: {name}, цена: {price}")

    def __str__(self):
        return self.name + ", Цена: " + str(self.price) + " руб., Количество: " + str(self.quantity)

    def __repr__(self):
        return "Product('" + self.name + "', " + str(self.price) + ", " + str(self.quantity) + ")"

    def __len__(self):
        return len(self)

    def __lt__(self, other):
        if not isinstance(other, Product):
            return NotImplemented
        return self.price < other.price

    def __eq__(self, other):
        if not isinstance(other, Product):
            return False
        return self.name == other.name and self.price == other.price

    def sell(self, amount):
        if self.quantity < amount:
            raise InsufficientStockError(
                f"Товара недостаточно. На складе: {self.quantity}, требуется: {amount}"
            )
        self.quantity = self.quantity - amount

    def to_dict(self) -> dict:
            return {
                "name": self.name,
                "price": str(self.price),       # без подчёркивания, Decimal → str
                "quantity": self.quantity,
                "total_price": str(self.get_total_price)
            }

    def calculate_price(self, discount: DiscountStrategy):
        if discount is None:
            return self.price
        return discount.apply(self.price)

    @CachedProperty
    def get_total_price(self) -> Decimal:
        return self.price * Decimal(str(self.quantity))

    @classmethod
    def from_dict(cls, data):
        return cls(data["name"], data["price"], data["quantity"])

"""Тесты"""
def main():
    product_data = {"name": "pizza", "price": 2000, "quantity": 10}
    new_product = Product.from_dict(product_data)
    print(new_product)
    print(Product.calculate_price(new_product, PersentDiscount(10)))
    print(new_product.get_total_price)

    # Проверка регистрации
    print(ModelRegistryMeta._registry)
    # {"Product": <class 'Product'>, "Order": <class 'Order'>}

    # Использование to_dict()
    product = Product("Ноутбук", Decimal("1000"), 10)
    print(product.to_dict())  # {"name": "Ноутбук", "price": 1000}

if __name__ == "__main__":
    main()