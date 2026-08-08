from src.models.payment import CardPayment, PayPalPayment, Payment
from src.models.order import Order
from src.models.product import Product
from src.models.user import User
from src.models.exceptions import ValidationEmailError, NegativePriceError

def process_order_system():

    try:
        products: list[Product] = [
            Product("Cheese", 1500, 30),
            Product("Bread", 1000, 10)
        ]
        products[0].set_price(2000)
        sorted(products)
        for product in products:
            print(product)
    except: NegativePriceError("Цена не может быть отрицательной")

    try:
        user = User("Sergey", "example@yandex.ru")
        order = Order(user, [], 0)
        order.add_product(Product("Cheese", 1500, 3), 10)
        order.add_product(Product("Bread", 100, 10), 5)
        print(order)
    except: ValidationEmailError("Некорректно указан Email")

    try:
        payments: list[Payment] = [
            CardPayment(1000, "1234 4567 1234 4567"),
            PayPalPayment(1500, "example@yandex.ru")
        ]
        for payment in payments:
            payment.process_payment()
    except (NegativePriceError, ValidationEmailError) as e:
        print("Ошибка ввода данных: ", e)

if __name__ == "__main__":
    process_order_system()