# Файл src/utils/calculations.py
import time
from collections import defaultdict

class Product:
    def __init__(self, id, name, price):
        self.id = id
        self.name = name
        self.price = price

class Order:
    def __init__(self, id, created_at, total, user_id=0):
        self.id = id
        self.created_at = created_at
        self.total = total
        self.user_id = user_id

def create_products_catalog(products):
    return {product.id: product for product in products}

def find_product_fast(products_dict, product_id):
    return products_dict.get(product_id)

def calculate_total_orders(orders):
    return sum(order.total for order in orders)
    
def sort_orders_by_date(orders):
    sorted_orders = sorted(orders, key=lambda x: x.created_at)



def group_orders_by_user(orders):
    grouped = defaultdict(list)                # для нового ключа значение - пустой список
    for order in orders:
        grouped[order.user_id].append(order)   # ключ создаётся сам при первом обращении
    return grouped


def create_test_products(count):
    """Создать тестовые товары"""
    return [Product(i, f"Товар {i}", i * 100) for i in range(count)]

def create_test_orders(count):
    """Создать тестовые заказы"""
    from datetime import datetime, timedelta
    base_date = datetime(2024, 1, 1)
    return [
        Order(i, base_date + timedelta(days=i % 365), 1000 + i * 100)
        for i in range(count)
        ]


def benchmark_search():
    """Измерить производительность поиска в списке vs словаре"""
    products = create_test_products(100000)
    product_id = 500

    # Поиск в списке (медленный)
    start_time = time.time()
    result_list = None
    for product in products:
        if product.id == product_id:
            result_list = product
            break
    time_list = time.time() - start_time

    # Поиск в словаре (быстрый)
    products_dict = create_products_catalog(products)
    start_time = time.time()
    result_dict = products_dict.get(product_id)
    time_dict = time.time() - start_time

    speedup = time_list / time_dict if time_dict > 0 else 0

    print("=== Тест поиска товара ===")
    print(f"Поиск в списке: {time_list:.6f} сек")
    print(f"Поиск в словаре: {time_dict:.6f} сек")
    print(f"Ускорение: {speedup:.2f}x")
    print()

    return {
        "time_list": time_list,
        "time_dict": time_dict,
        "speedup": speedup
        }


def benchmark_sorting():
    """Измерить производительность сортировки"""
    import random
    orders = create_test_orders(10000)
    random.shuffle(orders)

    # Ручная сортировка (медленная, O(n²))
    def bubble_sort(items):
        items = items.copy()
        n = len(items)
        for i in range(n):
            for j in range(0, n - i - 1):
                if items[j].created_at > items[j + 1].created_at:
                    items[j], items[j + 1] = items[j + 1], items[j]
        return items

    start_time = time.time()
    sorted_manual = bubble_sort(orders)
    time_manual = time.time() - start_time

    # Сортировка через sorted() (быстрая, O(n log n))
    start_time = time.time()
    sorted_fast = sort_orders_by_date(orders)
    time_fast = time.time() - start_time

    speedup = time_manual / time_fast if time_fast > 0 else 0

    print("=== Тест сортировки заказов ===")
    print(f"Ручная сортировка: {time_manual:.4f} сек")
    print(f"Сортировка через sorted(): {time_fast:.4f} сек")
    print(f"Ускорение: {speedup:.2f}x")
    print()

    return {
        "time_manual": time_manual,
        "time_fast": time_fast,
        "speedup": speedup
        }

def benchmark_optimizations():
    """Измерить производительность всех оптимизированных функций"""
    print("=" * 50)
    print("БЕНЧМАРК ОПТИМИЗАЦИЙ")
    print("=" * 50)
    print()

    results = {}

    # Тест 1: Поиск товара
    results["search"] = benchmark_search()

    # Тест 2: Сортировка
    results["sorting"] = benchmark_sorting()

    # Тест 3: Расчет суммы заказов
    orders = create_test_orders(1000000)

    # Медленный подход (цикл)
    start_time = time.time()
    total_slow = 0
    for order in orders:
        total_slow += order.total
    time_slow = time.time() - start_time

    # Быстрый подход (sum с генератором)
    start_time = time.time()
    total_fast = calculate_total_orders(orders)
    time_fast = time.time() - start_time

    speedup = time_slow / time_fast if time_fast > 0 else 0

    print("=== Тест расчета суммы заказов ===")
    print(f"Цикл: {time_slow:.6f} сек")
    print(f"sum() с генератором: {time_fast:.6f} сек")
    print(f"Ускорение: {speedup:.2f}x")
    print()

    results["sum"] = {
        "time_slow": time_slow,
        "time_fast": time_fast,
        "speedup": speedup
        }

    print("=" * 50)
    print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 50)
    for test_name, metrics in results.items():
        if "speedup" in metrics:
            print(f"{test_name}: ускорение {metrics['speedup']:.2f}x")

    return results

if __name__ == "__main__":
    benchmark_optimizations()

