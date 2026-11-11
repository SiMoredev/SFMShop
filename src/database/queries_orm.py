# src/database/queries.py — текущие версии на сыром SQL (ЭТО переписываешь на ORM)
from typing import Optional
from pydantic import EmailStr
from decimal import Decimal

from requests import session
from src.database.models import OrderItems, Product, get_session, Order, User
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload, selectinload


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
        raise
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
        raise
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
    except Exception as e:
        session.rollback()
        raise
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


def create_order(user_id, product_id: int, quantity: int):
    """Создание заказа"""
    session = get_session()
    total = 0
    try:
        user = session.get(User, user_id, with_for_update=True)
        if not user:
            raise ValueError("Пользователь не найден")
        
        product_db = session.get(Product, product_id, with_for_update=True)
        if not product_db:
            raise ValueError("Товары не найдены")

        if quantity <= 0:
            raise ValueError("Количество не может быть отрицательным")
        
        if product_db.stock < quantity:
            raise ValueError("Товаров недостаточно на складе")
        
        total = product_db.price * quantity
        if user.balance < total:
            raise ValueError("Недостаточно средств на счете")
        
        order = Order(
            user_id=user.id,
            total=total,
            order_items=[
            OrderItems(product_id=product_db.id, quantity=quantity, price=product_db.price)
            ],)
        
        product_db.stock -= quantity
        user.balance -= total
        session.add(order)
        session.commit()
        order_id = order.id
        return order_id
    
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_order(order_id: int):
    session = get_session()
    try:
        order = session.get(Order, order_id)
        return order
    finally:
        session.close()


def delete_order(order_id: int):
    session = get_session()
    try:
        order = session.get(Order, order_id)
        if order is None:
            return False
        session.delete(order)
        session.commit()
        return True
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


def process_order(order_id: int):
    """Получить заказ, проверить и перевести в статус processing"""
    with get_session() as session:
        with session.begin():
            # 1. Получение заказа
            stmt = (
                select(Order)
                .options(selectinload(Order.order_items))
                .where(Order.id == order_id)
                .with_for_update()
            )
            order = session.execute(stmt).scalar_one_or_none()

            # 2. Валидация
            if order is None:
                return f"Заказ {order_id}: не найден"
            if order.status != "pending":
                return f"Заказ {order_id}: уже в статусе {order.status}"
            if not order.order_items:
                return f"Заказ {order_id}: нет позиций"

            items_total = sum(item.price * item.quantity for item in order.order_items)
            if items_total != order.total:
                order.status = "error"
                return f"Заказ {order_id}: сумма не совпадает ({order.total} != {items_total})"

            # 3. Обновление статуса
            order.status = "processing"

    return f"Заказ {order_id} обработан"