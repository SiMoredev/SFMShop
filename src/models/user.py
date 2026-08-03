from src.models.exceptions import ValidationEmailError

class User:

    def __init__(self, name, email):
        self.name = name
        self._email = email

    def set_email(self, email):
        if "@" not in email:
            raise ValidationEmailError("Неверный формат email")
        self._email = email

    def get_email(self):
        return self._email