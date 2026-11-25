from fastapi import APIRouter, Depends, HTTPException
from src.dependencies import get_user_service
from src.schemas.user import UserCreate, UserResponse
from src.services.user_service import UserService
from src.core.exceptions import NotUniqueEmailError

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate, service: UserService = Depends(get_user_service)):
    try:
        user = await service.create_user(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password
        )
    except NotUniqueEmailError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_product(user_id: int, service: UserService = Depends(get_user_service)):
    try:
        return await service.user_repo.get_by_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))