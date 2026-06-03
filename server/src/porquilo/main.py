from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from porquilo.routers.diary import router as diary_router
from porquilo.routers.entries import router as entries_router
from porquilo.routers.foods import router as foods_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = Config("/app/alembic.ini")
    command.upgrade(cfg, "head")
    yield


app = FastAPI(title="Porquilo", lifespan=lifespan)

app.include_router(foods_router)
app.include_router(entries_router)
app.include_router(diary_router)


@app.get("/health")
def health():
    return {"status": "ok"}
