# Пример: src/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cors_origins: list[str] = ["http://localhost:3000"]
    jwt_secret: str = "change-me-in-production"
    rate_limit_login: str = "5/minute"
    database_url: str = "sqlite:///./sfmshop.db"
    debug: bool = False

    class Config:
        env_file = ".env"


settings = Settings()