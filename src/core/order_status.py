# src/core/order_status.py
from src.core.exceptions import InvalidOrderError

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending":    {"processing", "cancelled"},
    "processing": {"paid", "cancelled"},
    "paid":       {"shipped"}, #Вернуть canselled когда появится функционал
    "shipped":    {"delivered"},
}


def change_status(order, new_status: str) -> None:
    """Сменить статус заказа или бросить InvalidOrderError."""
    if new_status not in ALLOWED_TRANSITIONS.get(order.status, set()):
        raise InvalidOrderError(f"Нельзя перевести заказ из '{order.status}' в '{new_status}'")
    order.status = new_status