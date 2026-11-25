# Пример: src/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    cors_origins: list[str] = ["http://localhost:3000"]
    jwt_secret: str # без значения по умолчанию: не задан в .env → ошибка при старте
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7
    rate_limit_login: str = "5/minute"
    database_url: str = "sqlite:///./sfmshop.db"
    debug: bool = False
    llm_api_key: str = "ollama"  # Ollama ключ не проверяет, но клиенту openai нужна непустая строка
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen2.5-coder:7b"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings() #type: ignore[call_arg]