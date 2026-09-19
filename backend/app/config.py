from urllib.parse import urlparse

from arq.connections import RedisSettings
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "purplelens"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-secret"
    jwt_algorithm: str = "HS256"
    frontend_origin: str = "http://localhost:3000"
    openai_api_key: str | None = None


settings = Settings()


def arq_redis_settings() -> RedisSettings:
    parsed = urlparse(settings.redis_url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int((parsed.path or "/0").strip("/") or 0),
        password=parsed.password,
    )
