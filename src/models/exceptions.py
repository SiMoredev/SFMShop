class SFMShopException(Exception):
    """Базовое исключение для проекта SFMShop"""
    pass


class InsufficientStockError(SFMShopException):
    """Товара недостаточно на складе"""
    pass


class InvalidOrderError(SFMShopException):
    """Заказ невалиден"""
    pass


class NegativePriceError(SFMShopException):
    """Цена не может быть отрицательной"""
    pass

class ValidationEmailError(SFMShopException):
    """Некорректно указан email"""
    pass

class ZeroQuantityError(SFMShopException):
    """Количество товаров не может равняться нулю"""
    pass