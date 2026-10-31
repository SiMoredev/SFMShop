# src/database/queries.py — текущие версии на сыром SQL (ЭТО переписываешь на ORM)
from http.client import TOO_EARLY
from typing import Optional
from pydantic import EmailStr
from decimal import Decimal

from requests import session
from src.database.models import OrderItems, Product, get_session, Order, User
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload


def create_user(name: str, email: EmailStr):
    """Создать пользователя"""
    session = get_session()
    try:
        user = User(name=name, email=email)
        session.add(user)
        session.commit()
        user_id = user.id
        return user_id
    except Exception as e:
        session.rollback()
    finally:
        session.close()


def get_user_by_id(user_id: int):
    session = get_session()
    try:
        user = session.get(User, user_id)
        if user is None:
            return None
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    finally:
        session.close()


def get_users(limit: int = 10, offset: int = 0):
    session = get_session()
    try:
        stmt = select(User).limit(limit).offset(offset)
        users = session.execute(stmt).unique().scalars().all()
        if users:
            return [{
                "id": user.id,
                "name": user.name,
                "email": user.email
            } for user in users]
    finally:
        session.close()


def add_product(name: str, price: Decimal, stock: int=0):
    session = get_session()
    try:
        product = Product(name=name, price=price, stock=stock)
        session.add(product)
        session.commit()
        product_id = product.id
        return {"id": product_id}
    except Exception as e:
        session.rollback()
    finally:
        session.close()

    
def update_product(product_id: int, name: str, price: Decimal, stock: int):
    session = get_session()
    try:
        session.execute(
            update(Product).where(Product.id == product_id)
            .values(name=name, price=price, stock=stock)
        )
        session.commit()
    finally:
        session.close()


def delete_product(product_id: int) -> bool:
    session = get_session()
    try:
        product = session.get(Product, product_id)
        if product is None:
            return False
        session.delete(product)
        session.commit()
        return True
    finally:
        session.close()

def get_products_page(limit: int = 10, offset: int = 0) -> Optional[list]:
    session = get_session()
    try:
        products = session.execute(select(Product).limit(limit).offset(offset)).scalars().all()
        return [{
            "id": product.id,
            "name": product.name,
            "price": float(product.price),
            "stock": product.stock
        } for product in products]
    finally:
        session.close()


def get_product_by_id(product_id) -> Optional[dict]:
    session = get_session()
    try:
        product = session.get(Product, product_id)
        if product is None:
            return None
        return {
            "id": product.id,
            "name": product.name,
            "price": float(product.price),
            "stock": product.stock
        }
    finally:
        session.close()


def get_user_orders(user_id):
    """Заказы пользователя"""
    session = get_session()
    try:
        stmt = select(User).options(joinedload(User.orders)).where(User.id == user_id)
        user = session.execute(stmt).unique().scalar_one_or_none()
        if user:
            return [{
                "id": order.id,
                "total": float(order.total),
                "created_at": order.order_date.isoformat()
            } for order in user.orders]
        return []
    finally:
        session.close()


def create_order(user_id, total):
    """Создание заказа"""
    session = get_session()
    try:
        order = Order(user_id=user_id, total=total)
        session.add(order)
        session.commit()
        order_id = order.id
        return order_id
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


def get_all_orders_with_users():
    """Все заказы с данными пользователей"""
    session = get_session()

    try:
        stmt = select(Order).options(joinedload(Order.user))
        orders = session.execute(stmt).scalars().unique().all()
        return [{
            "id": order.id,
            "total": float(order.total),
            "user_name": order.user.name,
            "user_email": order.user.email
        } for order in orders]
    finally:
        session.close()


def get_orders_with_products(user_id: int):
    session = get_session()
    try:
        stmt = (
            select(Order.id, Product.name, OrderItems.quantity, Product.price)
            .join(Order.order_items)
            .join(OrderItems.product)
            .where(Order.user_id == user_id)
        )
        orders = session.execute(stmt).all()
        return [{
            "id": order.id,
            "product_name": order.name,
            "quantity": order.quantity,
            "price": float(order.price),
        } for order in orders]
    finally:
        session.close()