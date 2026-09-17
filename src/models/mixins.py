import json

class LoggableMixin:
    """Миксин для логирования"""

    def log(self, message: str):
        class_name = self.__class__.__name__
        print(f"[{class_name}] {message}")


class SerializableMixin:
    """Миксин для JSON-сериализации"""

    def to_json(self):
        """Преобразовать объект в JSON-строку"""
        return json.dumps(
            {
                "class": self.__class__.__name__,
                "data": self.__dict__,
            },
            ensure_ascii=False,  # кириллица остаётся читаемой, а не \uXXXX
        )
