from src.models.exceptions import NegativePriceError, ValidationEmailError

class Payment:

    def __init__(self, amount):
        if amount < 0:
            raise NegativePriceError("Цена не может быть отрицательной")
        self.amount = amount

    def process_payment(self):
        raise NotImplementedError("Метод должен быть переопределен")

class CardPayment(Payment):

    def __init__(self, amount, card_number):
        super().__init__(amount)
        self.__card_number = card_number

    def process_payment(self):
        print(f"Оплата картой *{self.__card_number[-4:]}: {self.amount} руб.")


class PayPalPayment(Payment):

    def __init__(self, amount, email):
        super().__init__(amount)
        if "@" not in email:
            raise ValidationEmailError("Неверный формат email")
        self._email = email

    def process_payment(self):
        print(f"Оплата PayPal ({self._email}): {self.amount} руб.")
