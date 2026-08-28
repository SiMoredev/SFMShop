from src.models.exceptions import NegativePriceError, InsufficientStockError
from typing import Optional
from decimal import Decimal


class Product:

    def __init__(self, name: str, price: Decimal, quantity: int):
        self.name = name
        if price < 0:
            raise NegativePriceError("Цена не может быть отрицательной")
        self.price = price
        if quantity < 0:
            raise ValueError("Количество не может быть отрицательным")
        self.quantity = quantity
        self.id: Optional[int] = None

    def __str__(self):
        return "Товар: " + self.name + ", Цена: " + str(self.price) + " руб., Количество: " + str(self.quantity)

    def __repr__(self):
        return "Product('" + self.name + "', " + str(self.price) + ", " + str(self.quantity) + ")"

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

    def get_total_price(self):
        return self.price * self.quantity
