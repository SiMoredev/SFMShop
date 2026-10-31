# Файл src/database/connection.py
from contextlib import contextmanager
import psycopg2
import os
from dotenv import load_dotenv
from src.api.models.exceptions import ValidationEmailError
from decimal import Decimal
import redis


load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "sfmshop"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
}

PRIMARY_DB = {
    "host": os.getenv("DB_PRIMARY_HOST", "localhost"),
    "port": os.getenv("DB_PRIMARY_PORT", 5432),
    "database": os.getenv("DB_NAME", "sfmshop"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD")
}

REPLICA_DB = {
    "host": os.getenv("DB_REPLICA_HOST", "localhost"),
    "port": os.getenv("DB_REPLICA_PORT", 5433),
    "database": os.getenv("DB_NAME", "sfmshop"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD")
}

# Подключение к Redis
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True # Автоматическое декодирование строк
    )

def connect_to_db(explain_slower_than_ms=None):
    """Подключение к базе данных PostgreSQL"""
    conn = psycopg2.connect(**DB_CONFIG)
    if explain_slower_than_ms is not None:
        with conn.cursor() as cur:
            cur.execute("LOAD 'auto_explain'")
            cur.execute("SET auto_explain.log_min_duration = %s", (explain_slower_than_ms,))
            cur.execute("SET auto_explain.log_analyze = on")   # реальное время, а не только оценка
            cur.execute("SET auto_explain.log_buffers = on")   # чтение с диска / из кеша
            cur.execute("SET auto_explain.log_format = 'json'")
        conn.commit()
    return conn

@contextmanager
def get_connection(read_only=False):

    if read_only:
        conn = psycopg2.connect(**REPLICA_DB)
    else:
        conn = psycopg2.connect(**PRIMARY_DB)

    try:
        yield conn
        if not read_only:
            conn.commit()
    except Exception as e:
        if not read_only:
            conn.rollback()
        raise
    finally:
        conn.close()

def test_connection():
    """Проверить подключение к базе данных"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"Подключение успешно! Версия PostgreSQL: {version[0]}")

def create_user(conn, name: str, email: str):
    if "@" not in email or "." not in email:
        raise ValidationEmailError(f"Некорректный формат email: {email}")
    
    with conn.cursor() as cur:
        try:
            cur.execute(
                "INSERT INTO users (name, email) VALUES (%s, %s)", (name, email)
            )
            conn.commit()
            return f"Пользователь {name}, {email} успешно создан"
        except psycopg2.errors.UniqueViolation:
            conn.rollback()


def get_users(conn, limit: int = 10, offset: int = 0):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, email FROM users LIMIT %s OFFSET %s", (limit, offset)
        )
        result = cur.fetchall()
        return result if result else []


def get_user_by_id(conn, id: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, email FROM users WHERE id = (%s)", (id,)
        )
        result = cur.fetchone()
        return result if result is not None else None


def create_order(conn, user_id: int, total: Decimal):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO orders (user_id, total) VALUES (%s, %s)", (user_id, total)
        )
        conn.commit()
        return cur.rowcount


def delete_order(conn, order_id: int):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM orders WHERE id = (%s)", (order_id,)
        )
        result = cur.rowcount()
        return result if result == 0 else []


def get_all_orders(conn, user_id: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, user_id, total FROM orders WHERE user_id = %s", (user_id,)
        )
        result = cur.fetchall()
        return result if result else []


def add_product(conn, name: str, price: Decimal, quantity: int):
    with conn.cursor() as cur:
        try:
            cur.execute(
                "INSERT INTO products (name, price, quantity) VALUES (%s, %s, %s) RETURNING id", (name, price, quantity)
            )
            (new_id,) = cur.fetchone()
            conn.commit()
            return {"id": new_id}
        except psycopg2.errors.UniqueViolation:
            conn.rollback()


def get_product_by_id(conn, product_id: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT name, price, stock FROM products WHERE id = %s", (product_id,)
        )
        product = cur.fetchone()
        return product if product is not None else None


def get_all_products(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT name, price, quantity FROM products"
        )
        products = cur.fetchall()
        return products if products else []


def get_products_page(conn, limit: int = 10, offset: int = 0):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, price, quantity FROM products ORDER BY id ASC LIMIT %s OFFSET %s", (limit, offset)
        )
        return cur.fetchall()


def count_products(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM products"
        )
        return cur.fetchone()[0]


def update_product_db(conn, product_id: int, name: str, price: Decimal, quantity: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE products 
            SET name = %s, price = %s, quantity = %s
            WHERE id = %s
            """, 
            (name, price, quantity, product_id)
        )
        conn.commit()
        return f"Цена товара id = {product_id} изменена. Назначенная стоимость: {price} руб."


def delete_product_db(conn, product_id: int):
    """Удалить товар по id, вернуть число удалённых строк (0 = не найден)."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        return cur.rowcount