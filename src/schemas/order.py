from pydantic import BaseModel, Field
from decimal import Decimal


class OrderCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    price: Decimal

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total: Decimal
    status: str
    items: list[OrderItemResponse] = Field(validation_alias="order_items")

    model_config = {"from_attributes": True}