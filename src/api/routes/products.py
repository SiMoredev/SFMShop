from fastapi import APIRouter, Depends, HTTPException, Query, Response
from src.dependencies import get_product_service
from src.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/{product_id}")
async def get_product(
    response: Response,
    product_id: int, 
    service: ProductService = Depends(get_product_service)
    ):
    product = await service.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Товар {product_id} не найден")
    response.headers["Cache-Control"] = "max-age=3600"
    return product

@router.get("/")
async def get_products(
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100), 
    service: ProductService = Depends(get_product_service),
    ):
    response.headers["Cache-Control"] = "max-age=3600"
    products = await service.get_products(skip, limit)
    return products
