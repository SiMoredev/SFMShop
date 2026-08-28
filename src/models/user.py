class User:

    def __init__(self, name, email):
        self.name = name
        if "@" not in email:
            raise ValueError("Неверный формат email")
        self.email = email

    def get_info(self):
        return 'Пользователь: ' + self.name + ', Email: ' + self.email

# TODO: проверять, что в email есть @ и точка
