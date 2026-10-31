# Файл src/database/queries.py
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_REPEATABLE_READ, ISOLATION_LEVEL_SERIALIZABLE
from psycopg2.errors import SerializationFailure
from src.api.models.mixins import LoggableMixin
from src.database.connection import connect_to_db
import time
import statistics
from contextlib import contextmanager
from psycopg2.extras import RealDictCursor

load_dotenv()

def get_orders_with_products(conn, user_id):
    cursor = conn.cursor()
    cursor.execute(
        """SELECT o.id, p.name, oi.quantity, p.price FROM orders o
        INNER JOIN order_items oi ON o.id = oi.order_id
        INNER JOIN products p ON oi.product_id = p.id
        WHERE o.user_id = (%s);""", (user_id,)
    )
    result = cursor.fetchall()
    cursor.close()
    return result

def get_order_statistics(conn):
    cursor = conn.cursor()
    cursor.execute(
        """SELECT user_id, COUNT(user_id) as order_count, SUM(total) as total_sum FROM orders
        GROUP BY user_id
        ORDER BY total_sum DESC;"""
    )
    result = cursor.fetchall()
    cursor.close()
    return result

def get_user_orders_history(conn, user_id):
    cursor = conn.cursor()
    cursor.execute(
        """SELECT u.name, p.name, oi.quantity, p.price FROM users u
        INNER JOIN orders o ON o.user_id = u.id
        INNER JOIN order_items oi ON oi.order_id = o.id
        INNER JOIN products p ON oi.product_id = p.id
        WHERE o.user_id = (%s);""", (user_id,)
    )
    result = cursor.fetchall()
    cursor.close()
    return result

def get_top_products(conn, limit=5):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            products.name,
            SUM(order_items.quantity) as total_sold
        FROM products
        INNER JOIN order_items ON products.id = order_items.product_id
        GROUP BY products.id, products.name
        ORDER BY total_sold DESC
        LIMIT %s
    """, (limit,))
    results = cursor.fetchall()
    cursor.close()
    return results    


def read_user_balance(user_id):

    with connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
            result = cur.fetchone()
            return result[0] if result else 0


def calculate_total_revenue(start_date, end_date):

    with connect_to_db() as conn:
    # Установка уровня изоляции
        conn.set_isolation_level(ISOLATION_LEVEL_REPEATABLE_READ)
        try:
            with conn.cursor() as cur:
                # Множественные чтения должны быть согласованными
                cur.execute(
                    "SELECT COALESCE(SUM(total), 0) FROM orders WHERE created_at BETWEEN %s AND %s",
                    (start_date, end_date)
                )
                total = cur.fetchone()[0] #type: ignore
                
                cur.execute(
                    "SELECT COUNT(*) FROM orders WHERE created_at BETWEEN %s AND %s",
                    (start_date, end_date)
                )
                count = cur.fetchone()[0] #type: ignore
                
                return {
                    "total": float(total),
                    "count": count,
                    "average": float(total) / count if count > 0 else 0
                }
        except psycopg2.Error as e:
            conn.rollback()
            raise


def critical_financial_operation(amount, from_user_id, to_user_id):

    with connect_to_db() as conn:
    # Установка уровня изоляции
        conn.set_isolation_level(ISOLATION_LEVEL_SERIALIZABLE)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT balance FROM users WHERE id = %s", (from_user_id,))
                row = cur.fetchone()
                if row is None:
                    raise ValueError("Пользователь не найден")
                balance = row[0]
                if balance < amount:
                    raise ValueError("Недостаточно средств")

                cur.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (amount, to_user_id))
                if cur.rowcount == 0:
                    raise ValueError("Получатель не найден")
                
                cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (amount, from_user_id))

                cur.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (amount, to_user_id))
                conn.commit()
                return True
        except psycopg2.Error as e:
            conn.rollback()
            raise
        except ValueError as e:
            conn.rollback()
            raise

        for attempt in range(3):
            try:
                return critical_financial_operation(amount, from_user_id, to_user_id)
            except SerializationFailure:
                continue          # конфликт с другой транзакцией — пробуем ещё раз
        raise RuntimeError("Не удалось выполнить перевод")


def create_order(connection, user_id, product_id, quantity, total):
    """Создать заказ с гарантией ACID"""
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            # BEGIN транзакции (автоматически)
            connection.set_isolation_level(
                psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE
                )

            # Проверка баланса
            cursor.execute(
                "SELECT balance FROM users WHERE id = %s FOR UPDATE",
                (user_id,)
                )
            user = cursor.fetchone()
            if not user or user['balance'] < total:
                connection.rollback()
                raise ValueError("Недостаточно средств")

            # Создание заказа
            cursor.execute(
                """
                INSERT INTO orders (user_id, total, status)
                VALUES (%s, %s, 'pending')
                RETURNING id
                """,
                (user_id, total)
                )
            order_id = cursor.fetchone()['id']

            # Добавление товара в заказ
            cursor.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s)
                """,
                (order_id, product_id, quantity, total)
                )

            # Обновление баланса
            cursor.execute(
                "UPDATE users SET balance = balance - %s WHERE id = %s",
                (total, user_id)
                )

            # Обновление инвентаря
            cursor.execute(
                "UPDATE products SET stock = stock - %s WHERE id = %s",
                (quantity, product_id)
                )

            # COMMIT транзакции
            connection.commit()
            return order_id

    except Exception as e:
        connection.rollback()
        raise e

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

# До оптимизации
def get_user_orders(user_id):
    """Получить заказы пользователя (медленно без индекса)"""
    with connect_to_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                EXPLAIN ANALYZE
                SELECT * FROM orders WHERE user_id = %s
                """,
                (user_id,)
                )
            plan = cursor.fetchall()
            print("План запроса до индекса:")
            for row in plan:
                print(row['QUERY PLAN'])

            cursor.execute(
                "SELECT * FROM orders WHERE user_id = %s",
                (user_id,)
                )
            return cursor.fetchall()

# Создание индекса
def create_indexes(connection):
    """Создать индексы для оптимизации"""
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)"
            )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date)"
            )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id)"
            )
        connection.commit()

# После оптимизации
def get_user_orders_optimized(connection, user_id):
    """Получить заказы пользователя (быстро с индексом)"""
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            EXPLAIN ANALYZE
            SELECT * FROM orders WHERE user_id = %s
            """,
            (user_id,)
            )
        plan = cursor.fetchall()
        print("План запроса после индекса:")
        for row in plan:
            print(row['QUERY PLAN'])

        cursor.execute(
            "SELECT * FROM orders WHERE user_id = %s",
            (user_id,)
            )
        return cursor.fetchall()


if __name__ == "__main__":
    pass
    # measure_index_performance(Decimal("99999"))
