from src.api.models.metaclasses import ModelRegistryMeta

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

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value == str:
            self._name = value
        else: raise ValueError("Имя должно быть строкой")