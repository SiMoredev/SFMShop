from src.models.metaclasses import ModelRegistryMeta

class User(metaclass=ModelRegistryMeta):

    def __init__(self, name, email):
        self.name = name
        if "@" not in email:
            raise ValueError("Неверный формат email")
        self.email = email

    def __str__(self):
        return f"Пользователь: {self.name}, email: {self.email}"

    def get_info(self):
        return 'Пользователь: ' + self.name + ', Email: ' + self.email

