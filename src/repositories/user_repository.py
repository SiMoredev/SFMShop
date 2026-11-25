from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.core.exceptions import NotUniqueEmailError

from src.database.models import User


class UserRepository:
    """Репозиторий для работы с пользователями."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int, for_update: bool = False) -> User | None:
        query = select(User).where(User.id == user_id)
        if for_update:
            query = query.with_for_update()
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
            )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        ) -> list[User]:
        """Получить список пользователей с пагинацией."""
        result = await self.session.execute(
            select(User).offset(skip).limit(limit)
            )
        return list(result.scalars().all())

    async def create(self, user: User) -> User:
        """Создать нового пользователя."""
        self.session.add(user)
        try:
            await self.session.flush()
        except IntegrityError:
            raise NotUniqueEmailError(f"Email {user.email} уже существует")
        return user

    async def update_balance(
        self,
        user_id: int,
        balance_delta: int,
        ) -> None:
        """Обновить баланс пользователя."""
        user = await self.get_by_id(user_id)
        if user is None:
            raise ValueError(f"Пользователь {user_id} не найден")
        user.balance += balance_delta