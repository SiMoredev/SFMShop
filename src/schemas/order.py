from pydantic import BaseModel, Field, field_validator
from decimal import Decimal


class OrderCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

class OrderResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    total: float
    status: str

    class Config:
        from_attributes = True