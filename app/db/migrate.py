import asyncio
import logging

from app.config import configure_logging
from app.db import init_db


async def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Running database initialization")
    await init_db()
    logger.info("Database initialization completed")


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
