import time
import statistics
from contextlib import contextmanager
from decimal import Decimal
from src.database.connection import connect_to_db


def find_products_by_price(cur, price):
    cur.execute("SELECT name, price FROM products WHERE price = %s", (price,))
    return cur.fetchall()


def measure(func, *args, repeats=5):
    """Запускает func несколько раз и возвращает медиану времени в секундах."""
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        func(*args)
        times.append(time.perf_counter() - start)
    return statistics.median(times)


@contextmanager
def price_index(conn):
    """Создаёт индекс на время блока with и гарантированно удаляет его."""
    with conn.cursor() as cur:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_products_price ON products(price)")
    conn.commit()
    try:
        yield
    finally:
        with conn.cursor() as cur:
            cur.execute("DROP INDEX IF EXISTS idx_products_price")
        conn.commit()


def measure_index_performance(price, repeats=5):
    with connect_to_db() as conn, conn.cursor() as cur:
        slow = measure(find_products_by_price, cur, price, repeats=repeats)

        with price_index(conn):
            fast = measure(find_products_by_price, cur, price, repeats=repeats)

    print(
        f"Без индекса: {slow * 1000:.2f} мс\n"
        f"С индексом:  {fast * 1000:.2f} мс\n"
        f"Ускорение:   в {slow / fast:.1f} раз"
    )


if __name__ == "__main__":
    measure_index_performance(Decimal("99999"))