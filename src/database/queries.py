# Файл src/database/queries.py
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_REPEATABLE_READ, ISOLATION_LEVEL_SERIALIZABLE
from psycopg2.errors import SerializationFailure
from src.database.connection import connect_to_db

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


# def transfer_money(conn, transfer_value, from_user_id, to_user_id):
#     cursor = conn.cursor()
#     try:
#         cursor.executr("BEGIN")
#         cursor.execute("UPDATE users SET amount = amount - %s WHERE id = %s", (transfer_value, from_user_id))
#         cursor.execute("SELECT amount FROM users WHERE id = %s", (from_user_id,))
#         result = cursor.fetchone()
#         if result[0] < 0:
#             raise ValueError("Баланс не может быть отрицательным")
#         cursor.execute("UPDATE users SET amount = amount + %s WHERE id = %s", (transfer_value, to_user_id))
#         conn.commit()
#     except psycopg2.Error as e:
#         conn.rollback()
#         print(e)
#     except ValueError as e:
#         conn.rollback()
#         print(e)
#     finally:
#         conn.close()

from psycopg2.extensions import ISOLATION_LEVEL_REPEATABLE_READ, ISOLATION_LEVEL_SERIALIZABLE
from src.database.connection import connect_to_db

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


import psycopg2
from psycopg2 import errors


class OrderError(Exception):
    pass


def create_order(user_id: int, items: dict[int, int], max_retries: int = 3) -> int:
    """items: {product_id: quantity}. Возвращает id созданного заказа."""
    if not items or any(qty <= 0 for qty in items.values()):
        raise ValueError("Некорректный состав заказа")

    for attempt in range(max_retries):
        conn = connect_to_db()
        try:
            # BEGIN psycopg2 отправит сам перед первым запросом
            with conn.cursor() as cur:
                # 1. Проверяем баланс, блокируя строку пользователя
                cur.execute("SELECT balance FROM users WHERE id = %s FOR UPDATE", (user_id,))
                row = cur.fetchone()
                if row is None:
                    raise OrderError("Пользователь не найден")
                balance = row[0]

                # Блокируем товары в фиксированном порядке, чтобы не было дедлоков
                product_ids = sorted(items)
                cur.execute(
                    "SELECT id, price, quantity FROM products "
                    "WHERE id = ANY(%s) ORDER BY id FOR UPDATE",
                    (product_ids,),
                )
                stock = {pid: (price, qty) for pid, price, qty in cur.fetchall()}

                missing = set(product_ids) - stock.keys()
                if missing:
                    raise OrderError(f"Товары не найдены: {missing}")
                for pid, qty in items.items():
                    if stock[pid][1] < qty:
                        raise OrderError(f"Недостаточно товара {pid} на складе")

                # Сумму считаем по ценам из БД, а не по данным от клиента
                total = sum(stock[pid][0] * qty for pid, qty in items.items())
                if balance < total:
                    raise OrderError("Недостаточно средств")

                # 2. Создаём заказ
                cur.execute(
                    "INSERT INTO orders (user_id, total) VALUES (%s, %s) RETURNING id",
                    (user_id, total),
                )
                order_id = cur.fetchone()[0]

                # 3. Добавляем товары в заказ (фиксируем цену на момент покупки)
                cur.executemany(
                    "INSERT INTO order_items (order_id, product_id, quantity, price) "
                    "VALUES (%s, %s, %s, %s)",
                    [(order_id, pid, qty, stock[pid][0]) for pid, qty in items.items()],
                )

                # 4. Списываем баланс
                cur.execute(
                    "UPDATE users SET balance = balance - %s WHERE id = %s",
                    (total, user_id),
                )

                # 5. Обновляем остатки
                cur.executemany(
                    "UPDATE products SET quantity = quantity - %s WHERE id = %s",
                    [(qty, pid) for pid, qty in items.items()],
                )

            conn.commit()  # COMMIT
            return order_id

        except (errors.SerializationFailure, errors.DeadlockDetected):
            conn.rollback()  # конфликт конкурентных транзакций, пробуем ещё раз
            continue
        except Exception:
            conn.rollback()  # ROLLBACK при любой другой ошибке
            raise
        finally:
            conn.close()

    raise OrderError("Не удалось создать заказ: превышено число попыток")


import json
from decimal import Decimal

from psycopg2 import errors


class OrderError(Exception):
    pass


# def create_order_AI(conn, user_id: int, cart: dict[int, int],
#                  shipping_address: str, idempotency_key: str) -> int:
#     """cart: {product_id: quantity}. Возвращает id заказа (новый или уже существующий)."""
#     if not cart or any(q <= 0 for q in cart.values()):
#         raise ValueError("Пустая корзина или некорректное количество")

#     product_ids = sorted(cart)

#     try:
#         with conn.cursor() as cur:
#             cur.execute("SET LOCAL lock_timeout = '3s'")

#             # 1. Блокируем товары в порядке id, защита от дедлоков
#             cur.execute(
#                 """SELECT id, price, quantity FROM products
#                    WHERE id = ANY(%s) AND is_active
#                    ORDER BY id FOR UPDATE""",
#                 (product_ids,),
#             )
#             stock = {pid: (price, qty) for pid, price, qty in cur.fetchall()}

#             # 2. Проверки и сумма по ценам из БД
#             missing = set(product_ids) - stock.keys()
#             if missing:
#                 raise OrderError(f"Товары недоступны: {sorted(missing)}")
#             short = [pid for pid in product_ids if stock[pid][1] < cart[pid]]
#             if short:
#                 raise OrderError(f"Недостаточно на складе: {short}")
#             total = sum((stock[pid][0] * cart[pid] for pid in product_ids), Decimal(0))

#             # 3. Заказ. При повторном запросе с тем же ключом вставки не будет
#             cur.execute(
#                 """INSERT INTO orders (user_id, status, total, shipping_address, idempotency_key)
#                    VALUES (%s, 'awaiting_payment', %s, %s, %s)
#                    ON CONFLICT (user_id, idempotency_key) DO NOTHING
#                    RETURNING id""",
#                 (user_id, total, shipping_address, idempotency_key),
#             )
#             row = cur.fetchone()
#             if row is None:
#                 # Такой заказ уже создан: откатываемся и возвращаем его
#                 conn.rollback()
#                 with conn.cursor() as cur2:
#                     cur2.execute(
#                         "SELECT id FROM orders WHERE user_id = %s AND idempotency_key = %s",
#                         (user_id, idempotency_key),
#                     )
#                     return cur2.fetchone()[0]
#             order_id = row[0]

#             # 4. Позиции со снимком цены
#             cur.executemany(
#                 """INSERT INTO order_items (order_id, product_id, quantity, price)
#                    VALUES (%s, %s, %s, %s)""",
#                 [(order_id, pid, cart[pid], stock[pid][0]) for pid in product_ids],
#             )

#             # 5. Резервируем остатки
#             cur.executemany(
#                 "UPDATE products SET quantity = quantity - %s WHERE id = %s",
#                 [(cart[pid], pid) for pid in product_ids],
#             )

#             # 6. Событие для воркера (письмо, склад, аналитика)
#             cur.execute(
#                 "INSERT INTO outbox (event_type, payload) VALUES (%s, %s)",
#                 ("order_created", json.dumps({"order_id": order_id, "user_id": user_id})),
#             )

#         conn.commit()
#         return order_id

#     except Exception:
#         conn.rollback()
#         raise
            
# Файл src/database/queries.py
import time
import statistics
from contextlib import contextmanager
from decimal import Decimal


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