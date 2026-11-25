# Файл src/services/product_service.py
from src.database.models import User
from src.repositories.user_repository import UserRepository
from src.core.security import hash_password
import asyncio
from src.core.security import hash_password, verify_password


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def create_user(self, name: str, email: str, password: str) -> User:
        """Создать пользователя (Эндпоинт POST /users)"""
        hashed = await asyncio.to_thread(hash_password, password)
        user = User(
            name=name,
            email=email,
            hashed_password=hashed,
        )
        return await self.user_repo.create(user)

    async def authenticate(self, email: str, password: str) -> User | None:
        """Вернуть пользователя, если email и пароль верные, иначе None."""
        user = await self.user_repo.get_by_email(email)
        if user is None:
            return None
        is_valid = await asyncio.to_thread(verify_password, password, user.hashed_password)
        return user if is_valid else None

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Получить пользователя по ID (эндпоинт GET /users/{user_id})."""
        return await self.user_repo.get_by_id(user_id)

    async def get_users(self, skip: int, limit: int):
        """Получить список пользователей"""
        return await self.user_repo.get_all(skip, limit)