from fastapi import APIRouter, Depends, HTTPException
from src.dependencies import get_product_service
from src.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{product_id}")
async def get_product(product_id: int, service: ProductService = Depends(get_product_service)):
    try:
        return await service.product_repo.get_by_id(product_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))