from typing import Generic, TypeVar, Any
from decimal import Decimal

T = TypeVar('T', int, float, Decimal)

class PositiveNumber(Generic[T]):
    """Дескриптор для валидации положительных чисел"""
    
    def __init__(self, name):
        self.name = name

    def __get__(self, instance: Any, owner: Any = None) -> T:
        if instance is None:
            return self # type: ignore
        return getattr(instance, self.name)

    def __set__(self, instance: Any, value: T) -> None:
        if value < 0:
            raise ValueError(f"{self.name} не может быть отрицательным")
        setattr(instance, self.name, value)

class CachedProperty:

    def __init__(self, func):
        self.func = func
        self.name = func.__name__

    def __get__(self, instance, owner):
        cache_attr = f"_cashed_{self.name}"
        if hasattr(instance, cache_attr):
            return getattr(instance, cache_attr)
        value = self.func(instance)
        setattr(instance, cache_attr, value)
        return value