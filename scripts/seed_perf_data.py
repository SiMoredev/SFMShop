"""Наполнение БД тестовыми данными для проверки производительности запросов.

Добивает каждую таблицу (users, products, orders, order_items) до TARGET строк.
Данные согласованы между собой:
- orders.user_id ссылается на существующих пользователей;
- у каждого нового заказа есть хотя бы одна позиция;
- order_items.price равна цене товара, orders.total = сумма quantity * price;
- дата заказа позже даты регистрации пользователя.

Запуск из корня проекта (по умолчанию до 1 000 000 строк):
    python -m scripts.seed_perf_data
    python -m scripts.seed_perf_data 10000000
"""
import sys
import time

from sqlalchemy import text

from src.database.models import engine

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000

STATUSES = "ARRAY['pending', 'paid', 'shipped', 'delivered', 'cancelled']"


def missing(conn, table: str) -> int:
    count = conn.execute(text(f"SELECT count(*) FROM {table}")).scalar()
    return max(TARGET - count, 0)


def seed_users(conn, n: int) -> None:
    # Email строится от max(id), чтобы повторный запуск не нарушал UNIQUE (email)
    conn.execute(text("""
        INSERT INTO users (name, email, balance, created_at)
        SELECT
            'Test User ' || (start + g),
            'perf_user_' || (start + g) || '@example.test',
            round((random() * 10000)::numeric, 2),
            now() - interval '3 years' + random() * interval '1 year'
        FROM generate_series(1, :n) AS g,
             (SELECT coalesce(max(id), 0) AS start FROM users) AS s
    """), {"n": n})


def seed_products(conn, n: int) -> None:
    conn.execute(text("""
        INSERT INTO products (name, price, stock, created_at)
        SELECT
            'Test Product ' || (start + g),
            round((1 + random() * 9999)::numeric, 2),
            floor(random() * 1000)::int,
            now() - interval '3 years' + random() * interval '1 year'
        FROM generate_series(1, :n) AS g,
             (SELECT coalesce(max(id), 0) AS start FROM products) AS s
    """), {"n": n})


def seed_orders(conn, n: int) -> int:
    """Создаёт заказы с total = 0 и возвращает id, после которого начинаются новые."""
    first_id = conn.execute(text("SELECT coalesce(max(id), 0) FROM orders")).scalar()
    conn.execute(text(f"""
        INSERT INTO orders (user_id, total, order_date, status)
        SELECT
            u.ids[1 + floor(random() * u.cnt)::int],
            0,
            now() - random() * interval '2 years',
            ({STATUSES})[1 + floor(random() * 5)::int]
        FROM generate_series(1, :n) AS g,
             (SELECT array_agg(id) AS ids, count(*) AS cnt FROM users) AS u
    """), {"n": n})
    fix_order_dates(conn, first_id)
    return first_id


def fix_order_dates(conn, first_order_id: int) -> None:
    # Старые пользователи могли зарегистрироваться недавно — сдвигаем дату их заказов
    conn.execute(text("""
        UPDATE orders o
        SET order_date = u.created_at + random() * (now() - u.created_at)
        FROM users u
        WHERE o.id > :first AND u.id = o.user_id AND o.order_date < u.created_at
    """), {"first": first_order_id})


def seed_order_items(conn, n: int, first_order_id: int) -> None:
    # Первые позиции покрывают каждый новый заказ по разу, остальные идут по кругу,
    # так что пустых заказов не остаётся. Если новых заказов нет, берём все заказы.
    conn.execute(text("""
        CREATE TEMP TABLE target_orders ON COMMIT DROP AS
        SELECT row_number() OVER (ORDER BY id) - 1 AS rn, id
        FROM orders
        WHERE id > CASE WHEN EXISTS (SELECT 1 FROM orders WHERE id > :first)
                        THEN :first ELSE 0 END
    """), {"first": first_order_id})
    conn.execute(text("CREATE INDEX ON target_orders (rn)"))
    conn.execute(text("""
        INSERT INTO order_items (order_id, product_id, quantity, price)
        SELECT o.id, p.id, x.quantity, p.price
        FROM (
            SELECT
                g,
                pr.ids[1 + floor(random() * pr.cnt)::int] AS product_id,
                1 + floor(random() * 5)::int AS quantity
            FROM generate_series(0, :n - 1) AS g,
                 (SELECT array_agg(id) AS ids, count(*) AS cnt FROM products) AS pr
        ) AS x
        JOIN target_orders o ON o.rn = x.g % (SELECT count(*) FROM target_orders)
        JOIN products p ON p.id = x.product_id
    """), {"n": n})
    conn.execute(text("""
        UPDATE orders o
        SET total = s.total
        FROM (
            SELECT order_id, sum(quantity * price) AS total
            FROM order_items
            WHERE order_id IN (SELECT id FROM target_orders)
            GROUP BY order_id
        ) AS s
        WHERE o.id = s.order_id
    """))


def step(name: str, fn, *args):
    started = time.perf_counter()
    result = fn(*args)
    print(f"{name}: {time.perf_counter() - started:.1f} c")
    return result


def main() -> None:
    with engine.begin() as conn:
        n_users = missing(conn, "users")
        n_products = missing(conn, "products")
        n_orders = missing(conn, "orders")
        n_items = missing(conn, "order_items")
        print(f"Добавим: users={n_users}, products={n_products}, "
              f"orders={n_orders}, order_items={n_items}")

        if n_users:
            step("users", seed_users, conn, n_users)
        if n_products:
            step("products", seed_products, conn, n_products)
        first_order_id = conn.execute(text("SELECT coalesce(max(id), 0) FROM orders")).scalar()
        if n_orders:
            first_order_id = step("orders", seed_orders, conn, n_orders)
        if n_items:
            step("order_items + totals", seed_order_items, conn, n_items, first_order_id)

    # ANALYZE вне транзакции, чтобы планировщик сразу видел новую статистику
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        step("analyze", conn.execute, text("ANALYZE users, products, orders, order_items"))


if __name__ == "__main__":
    main()
