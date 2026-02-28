from functools import lru_cache
import os
import dotenv

dotenv.load_dotenv(".env")


class Settings:
    def __init__(self) -> None:
        # Application settings
        self.app_name: str = os.getenv("APP_NAME", "ETLEventDriven")
        self.app_env: str = os.getenv("APP_ENV", "development")
        self.app_debug: bool = os.getenv("APP_DEBUG", "true").lower() == "true"

        # API settings
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))

        # Postgres settings
        self.postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
        self.postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
        self.postgres_db: str = os.getenv("POSTGRES_DB", "")
        self.postgres_user: str = os.getenv("POSTGRES_USER", "")
        self.postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")

        # Redis settings
        self.redis_host: str = os.getenv("REDIS_HOST", "localhost")
        self.redis_port: int = int(os.getenv("REDIS_PORT", "6379"))

        # RabbitMQ settings
        self.rabbitmq_host: str = os.getenv("RABBITMQ_HOST", "localhost")
        self.rabbitmq_port: int = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.rabbitmq_user: str = os.getenv("RABBITMQ_USER", "")
        self.rabbitmq_password: str = os.getenv("RABBITMQ_PASSWORD", "")

        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def database_url(self) -> str:
        # Build asynchronous PostgreSQL DSN from individual parts
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # Return cached Settings instance to avoid re-reading environment variables
    return Settings()
