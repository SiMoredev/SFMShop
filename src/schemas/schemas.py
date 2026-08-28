from pydantic import BaseModel
from decimal import Decimal

class OrderCreate(BaseModel):
    user_id: int
    product_id: int

class UserCreate(BaseModel):
    name: str
    email: str

class ProductCreate(BaseModel):
    name: str
    price: Decimal
    quantity: int

class ProductUpdate(BaseModel):
    name: str
    price: Decimal
    quantity: int