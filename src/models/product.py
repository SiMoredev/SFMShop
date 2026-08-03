from src.models.exceptions import NegativePriceError

class Product:

    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

    def __str__(self) -> str:
        return f"Товар: {self.name}, Цена: {self.price} руб., Количество: {self.quantity}"

    def __repr__(self) -> str:
        return f"Product('{self.name}', {self.price}, {self.quantity})"

    def __lt__(self, other):
        return self.price * self.quantity < other.price * other.quantity

    def __eq__(self, other):
        return self.name == other.name & self.price == other.price

    def set_price(self, price):
        if price < 0:
            raise NegativePriceError("Цена не может быть отрицательной")
        self.price = price