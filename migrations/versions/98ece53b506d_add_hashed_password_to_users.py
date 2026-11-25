"""add hashed_password to users

Revision ID: 98ece53b506d
Revises: 8a4f342edc2f
Create Date: 2026-11-24 14:31:15.834178

"""
import os
from typing import Sequence, Union

import bcrypt
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98ece53b506d'
down_revision: Union[str, Sequence[str], None] = '8a4f342edc2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Общий стартовый пароль для всех существующих пользователей берём из .env,
    # чтобы не хранить его открытым текстом в коде миграции.
    password = os.getenv("DEFAULT_USER_PASSWORD")
    if not password:
        raise RuntimeError("Задайте DEFAULT_USER_PASSWORD в .env перед миграцией")

    # Хэшируем один раз: bcrypt намеренно медленный, 10 млн хэшей заняли бы недели.
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # ADD COLUMN ... NOT NULL DEFAULT <константа> в PostgreSQL 11+ выполняется
    # мгновенно: таблица не переписывается, значение берётся из метаданных.
    op.add_column(
        'users',
        sa.Column('hashed_password', sa.String(255), nullable=False, server_default=hashed),
    )
    # Убираем default: новые пользователи должны получать свой пароль, а не общий.
    op.alter_column('users', 'hashed_password', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'hashed_password')
