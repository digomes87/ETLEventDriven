import uvicorn
from fastapi import FastAPI

from app.config import configure_logging, get_settings
from app.middlewares.errors import register_error_middleware
from app.routes.api import router as api_router


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    application = FastAPI(title=settings.app_name, debug=settings.app_debug)

    register_error_middleware(application)
    application.include_router(api_router, prefix="/api")

    return application


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    run()
