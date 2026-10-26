# src/database/queries.py — текущие версии на сыром SQL (ЭТО переписываешь на ORM)
from src.database.models import get_session, Order, User
from sqlalchemy import select
from sqlalchemy.orm import joinedload


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
                "created_at": order.created_at.isoformat()
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