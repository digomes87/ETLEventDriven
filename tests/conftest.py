import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.routes.api as api_module
from app.db import get_db_session
from app.main import create_app
from app.models import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_etlpay.db"

engine_test = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = async_sessionmaker(bind=engine_test, expire_on_commit=False)

app = create_app()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_database() -> None:
    async with engine_test.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


async def override_get_db_session() -> AsyncSession:
    session: AsyncSession = TestSessionLocal()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="session")
def test_app():
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    app.dependency_overrides[get_db_session] = override_get_db_session
    return app


class DummyRedisClient:
    async def get(self, key: str) -> str | None:
        return None

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        return None


@pytest.fixture(autouse=True)
def mock_redis_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_module, "RedisCacheClient", DummyRedisClient)
