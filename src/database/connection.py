# Файл src/database/connection.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def connect_to_db():
    return psycopg2.connect(
        host = "localhost",
        database = "shop",
        user = "simore",
        password = os.getenv("DB_PASSWORD")
    )
        
def create_user(conn, name, email):
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s)", (name, email)
        )
        conn.commit()
        print(f"Пользователь создан. Имя: {name}, email: {email}")
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        print("Данный Email уже существует")
    finally:
        cursor.close()

def get_user_by_id(conn, id: int):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, email FROM users WHERE id = (%s)", (id,)
    )
    result = cursor.fetchone()
    if result is None:
        print("Пользователь под данным id не существует.")
    else:
        print(f"Найден пользователь: {result[0]}, {result[1]}")
        return {result[0]: result[1]}
    cursor.close()
        
def create_order(conn, user_id, products):
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT name, price, quantity FROM products WHERE name IN %s", (products,)
        )
        result = cursor.fetchall()
        if not result:
            raise ValueError(f"Ни один из товаров {products} не найден в базе")
        total = sum(row[1] * row[2] for row in result)
        cursor.execute(
            "DELETE FROM products WHERE name IN %s", (products,)
        )
        cursor.execute(
            "INSERT INTO orders (user_id, total) VALUES (%s, %s)", (user_id, total)
        )
        print(f"Заказ создан: user_id={user_id}, total={total}")
        conn.commit()
    except ValueError as e:
        print(e)
    finally:
        cursor.close()


# Здесь нужно подсчитать количество заказов и их общий тотал
def get_all_orders(conn, user_id):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, total FROM orders WHERE user_id = %s", (user_id,)
    )
    result = cursor.fetchall()
    if not result:
        print(f"Заказы пользователя {user_id} отсутствуют в базе")
    else:
        print(f"Заказы пользователя: {result}")
        return result
    cursor.close()

def add_product(conn, values):
    cursor = conn.cursor()
    try:
        cursor.executemany(
            "INSERT INTO products (name, price, quantity) VALUES (%s, %s, %s)", values
        )
        conn.commit()
        cursor.close()
        print(f"Товар добавлен: {values}")
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        print("Данные товары уже добавлены")
    finally:
        cursor.close()

def get_all_products(conn):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, price, quantity FROM products"
    )
    products = cursor.fetchall()
    if products:
        return products
    else:
        print("Отсутвуют товары для оформления заказа")
    cursor.close()

def update_product_price(conn, name, price):
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT name, price FROM products WHERE name = (%s)", (name,)
        )
        result = cursor.fetchone()
        if result is None:
            raise ValueError("Товар с данным наименованием отсутствует в базе")
        else:
            print(f"Товар: {result[0][0]}, цена {result[0][1]}")
            cursor.execute(
                "UPDATE products SET price = (%s) WHERE name = (%s)", (price, name)
            )
            print(f"Цена товара {name} изменена. Назначенная стоимость: {price} руб.")
            conn.commit()
    except ValueError as e:
        print(e)
    finally: cursor.close()

def main(add_products, update_values, new_price):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        add_product(conn, add_products)
        products = get_all_products(conn)
        print("Все товары:")
        if products is not None:
            for product in products:
                print(f"Название: {product[0]}, цена: {product[1]} руб., количество {product[2]} шт.")
        update_product_price(conn, update_values, new_price)
    except ValueError as e:
        print(e)
    finally:
        cursor.close()

values = (
    ("Шоколад11", 1500, 3),
    ("Хлеб11", 100, 10),
    ("Сыр11", 150, 100)
)

# if __name__ == "__main__":
#     main(values, values[0][0], 2000)

name, price, quantity = zip(*values)

conn = connect_to_db()
create_user(conn, "Sergey", "exampley@gmail.com")
get_user_by_id(conn, 10)
create_order(conn, 10, name)
get_all_orders(conn, 10)

curs = conn.cursor()
curs.fetchone

