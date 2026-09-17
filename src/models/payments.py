from src.models.mixins import LoggableMixin, SerializableMixin
from abc import ABC, abstractmethod

class Payment(ABC):

    @abstractmethod
    def process(self):
        pass

class CardPayment(LoggableMixin, SerializableMixin, Payment):
    def __init__(self, amount):
        self.amount = amount
        self.log(f"Создан платеж: {amount}")
    
    def process(self):
        self.log("Обработка платежа")