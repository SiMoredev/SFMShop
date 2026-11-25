from pydantic import BaseModel, Field, field_validator
from decimal import Decimal


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: Decimal = Field(..., gt=0)
    stock: int = Field(..., ge=0)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Название не может быть пустым')
        return v.strip()


class ProductUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Название товара")
    price: Decimal = Field(..., gt=0, description="Цена товара")
    stock: int = Field(..., ge=0, description="Количество на складе")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Название не может быть пустым")
        return v.strip()


class ProductResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    stock: int

    model_config = {"from_attributes": True}