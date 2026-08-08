from src.models.product import Product

class Order:

    def __init__(self, user, products, total, discount=0.0):
        self.user = user
        self.products = products
        self.total = total
        self.discount = discount

    def __str__(self) -> str:
        return f"Заказ пользователя {self.user.name} на сумму {self.total} руб."

    def add_product(self, product, discount=0.0):
        if not isinstance(product, Product):
            raise TypeError("объект не является экземпляром класса Product")
        self.products.append(product)
        self.total += product.price * product.quantity * (1 - discount)