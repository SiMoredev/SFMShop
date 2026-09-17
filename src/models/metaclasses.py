# Файл src/models/metaclasses.py
class ModelRegistryMeta(type):
    """Метакласс, который автоматически регистрирует классы моделей в реестре"""
    _registry = {}

    def __new__(cls, name, bases, attrs):

        def to_dict(self):
            return self.__dict__

        if "to_dict" not in attrs and not any(hasattr(base, "to_dict") for base in bases):
            attrs["to_dict"] = to_dict

        new_class = super().__new__(cls, name, bases, attrs)

        if name != "ModelRegistryMeta":
            cls._registry[name] = new_class

        return new_class