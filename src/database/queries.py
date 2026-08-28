# Файл src/database/queries.py
from dotenv import load_dotenv

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