from fastapi import APIRouter, Depends, HTTPException

from src.core.exceptions import InsufficientFundsError, InsufficientStockError, InvalidOrderError
from src.database.models import User
from src.dependencies import get_current_user, get_order_service, get_payment_service
from src.schemas.order import OrderCreate, OrderResponse
from src.services.order_service import OrderService
from src.services.payment_service import PaymentService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    try:
        return await service.create_order(
            user_id=current_user.id,
            product_id=order_data.product_id,
            quantity=order_data.quantity,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientStockError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{order_id}/process", response_model=OrderResponse)
async def process_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    try:
        return await service.process_order(order_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidOrderError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{order_id}/pay", response_model=OrderResponse)
async def pay_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    try:
        return await service.pay_order(order_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientFundsError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except InvalidOrderError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    try:
        return await service.cancel_order(order_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidOrderError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    order = await service.get_order(order_id, user_id=current_user.id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Заказ {order_id} не найден")
    return order