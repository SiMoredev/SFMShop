# Файл src/api/auth.py
from fastapi import APIRouter, Depends, HTTPException
from src.api.models.user import User
from src.core.security import create_refresh_token, create_access_token, decode_token
from src.core.config import settings
from src.dependencies import get_current_user, get_user_service
from src.schemas.user import LoginRequest, UserCreate, UserResponse, TokenResponse, RefreshRequest
from src.core.exceptions import NotUniqueEmailError
from src.services.user_service import UserService
from fastapi import Depends, HTTPException
import jwt


router = APIRouter(prefix="/auth", tags=["auth"])

def _issue_tokens(user_id: int) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        expires_in=settings.access_token_ttl_minutes * 60
    )

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_data: UserCreate, 
    service: UserService = Depends(get_user_service)
    ):
    try:
        return await service.create_user(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
        )
    except NotUniqueEmailError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, service: UserService = Depends(get_user_service)):
    user = await service.authenticate(data.email, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    return _issue_tokens(user.id)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, service: UserService = Depends(get_user_service)):
    try:
        user_id = decode_token(data.refresh_token, expected_type="refresh")
    except jwt.InvalidTokenError:   # сюда же попадает истёкший токен
        raise HTTPException(status_code=401, detail="Недействительный refresh-токен")

    user = await service.get_user_by_id(user_id)
    if user is None:                 # пользователя удалили, пока жил токен
        raise HTTPException(status_code=401, detail="Недействительный refresh-токен")
    return _issue_tokens(user.id)

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user