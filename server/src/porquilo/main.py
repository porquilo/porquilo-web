import logging
import os
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from porquilo.core.errors import AUTH_ERROR_CODES, PorquiloError
from porquilo.core.limiter import limiter
from porquilo.routers.admin import router as admin_router
from porquilo.routers.auth import router as auth_router
from porquilo.routers.diary import router as diary_router
from porquilo.routers.entries import router as entries_router
from porquilo.routers.foods import router as foods_router
from porquilo.routers.meals import router as meals_router
from porquilo.routers.profile import router as profile_router
from porquilo.routers.settings import router as settings_router
from porquilo.routers.setup import router as setup_router
from porquilo.routers.sync import router as sync_router
from porquilo.routers.users import router as users_router
from porquilo.routers.version import router as version_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.path.exists("/app/alembic.ini"):
        cfg = Config("/app/alembic.ini")
        command.upgrade(cfg, "head")
    yield


app = FastAPI(title="Porquilo", lifespan=lifespan)

app.state.limiter = limiter


@app.exception_handler(PorquiloError)
async def porquilo_error_handler(request: Request, exc: PorquiloError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Validation failed.",
                "details": {"errors": jsonable_encoder(exc.errors())},
            }
        },
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    _, message = AUTH_ERROR_CODES["too_many_attempts"]
    return JSONResponse(
        status_code=429,
        content={"error": {"code": "too_many_attempts", "message": message, "details": {}}},
    )


@app.exception_handler(Exception)
async def catch_all_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "Something went wrong.", "details": {}}},
    )


# Bootstrap: the first account is created via an interactive setup wizard
# (POST /api/setup/init), gated by an empty `users` table. No env-var fallback.
app.include_router(auth_router, prefix="/api")
app.include_router(admin_router)
app.include_router(diary_router)
app.include_router(foods_router)
app.include_router(entries_router)
app.include_router(meals_router)
app.include_router(profile_router, prefix="/api")
app.include_router(settings_router)
app.include_router(setup_router, prefix="/api")
app.include_router(sync_router)
app.include_router(users_router, prefix="/api")
app.include_router(version_router)


@app.get("/health")
def health():
    return {"status": "ok"}
