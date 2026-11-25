from pydantic import BaseModel, Field, field_validator
from decimal import Decimal


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: Decimal = Field(..., gt=0)
    stock: int = Field(..., ge=0)


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

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        if not v or v == 0:
            raise ValueError("Цена товара должна быть указана и не равнятся 0")
        return v