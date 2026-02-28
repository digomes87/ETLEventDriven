import logging

from fastapi import Request
from fastapi.responses import JSONResponse


def register_error_middleware(app) -> None:
    @app.middleware("http")
    async def error_handling_middleware(request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception:
            logging.getLogger("etlpay").exception("Unhandled application error")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )