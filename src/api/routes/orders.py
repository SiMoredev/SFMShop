# Файл src/api/routes/orders.py
from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import get_order_service
from src.schemas.order import OrderCreate, OrderResponse
from src.api.models.exceptions import InsufficientStockError
from src.services.order_service import OrderService


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    service: OrderService = Depends(get_order_service),
    ):
    """Создание заказа."""
    try:
        order = await service.create_order(
            user_id=order_data.user_id,
            product_id=order_data.product_id,
            quantity=order_data.quantity,
            )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientStockError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return order


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    service: OrderService = Depends(get_order_service),
    ):
    """Отмена заказа."""
    try:
        order = await service.cancel_order(order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return order


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    service: OrderService = Depends(get_order_service),
    ):
    """Получение заказа по ID."""
    order = await service.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Заказ {order_id} не найден")
    return order