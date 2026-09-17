from src.models.product import Product, DiscountStrategy
from decimal import Decimal

class ProductCalculator:
    """Класс для расчета товаров"""

    @staticmethod
    def calculate_total_price(product: Product) -> Decimal:
        return product.get_total_price

    @staticmethod
    def apply_discount(product: Product, discount: DiscountStrategy) -> Decimal:
        return discount.apply(product.price)