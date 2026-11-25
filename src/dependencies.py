# Файл src/dependencies.py
import os
from collections.abc import AsyncGenerator
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from openai import AsyncOpenAI
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository
from src.services.cache_service import CacheService
from src.services.order_service import OrderService
from src.services.payment_service import PaymentService
from src.services.product_service import ProductService
from src.services.user_service import UserService
import jwt
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.core.security import decode_token
from src.database.models import User
from src.core.config import settings

bearer_scheme = HTTPBearer()

load_dotenv()

# Те же DB_* из .env, что и в src/database/models.py, но асинхронный драйвер asyncpg
ASYNC_DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', '')}@"
    f"{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'sfmshop')}"
    )

engine = create_async_engine(ASYNC_DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Сессия БД с автоматическим закрытием."""
    async with async_session() as session:
        async with session.begin():
            yield session

async def get_user_repository(session: AsyncSession = Depends(get_session)) -> UserRepository:
    """Репозиторий пользователей"""
    return UserRepository(session)

async def get_product_repository(session: AsyncSession = Depends(get_session)) -> ProductRepository:
    """Репозиторий товаров."""
    return ProductRepository(session)

async def get_order_repository(session: AsyncSession = Depends(get_session)) -> OrderRepository:
    """Репозиторий заказов."""
    return OrderRepository(session)

async def get_cache_service() -> CacheService:
    """Сервис кеширования Redis"""
    return CacheService()

async def get_user_service(user_repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(user_repo=user_repo)

async def get_product_service(
    product_repo: ProductRepository = Depends(get_product_repository),
    cache: CacheService = Depends(get_cache_service)
    ) -> ProductService:
    return ProductService(product_repo=product_repo, cache=cache)

async def get_order_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    product_repo: ProductRepository = Depends(get_product_repository),
    ) -> OrderService:
    """Сервис заказов со всеми зависимостями."""
    return OrderService(order_repo=order_repo, product_repo=product_repo)

async def get_payment_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    user_repo: UserRepository = Depends(get_user_repository)
    ) -> PaymentService:
    return PaymentService(order_repo=order_repo, user_repo=user_repo)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
    ) -> User:
    """Достать пользователя из заголовка Authorization: Bearer <access_token>."""
    try:
        user_id = decode_token(credentials.credentials, expected_type="access")
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Недействительный или истёкший токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user

async def get_llm_client():
    async with AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        max_retries=0,
    ) as client:
        yield client