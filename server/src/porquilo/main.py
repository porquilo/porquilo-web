from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from porquilo.routers.foods import router as foods_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = Config("/app/alembic.ini")
    command.upgrade(cfg, "head")
    yield


app = FastAPI(title="Porquilo", lifespan=lifespan)

app.include_router(foods_router)


@app.get("/health")
def health():
    return {"status": "ok"}
