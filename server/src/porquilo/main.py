from fastapi import FastAPI

from porquilo.routers.foods import router as foods_router

app = FastAPI(title="Porquilo")

app.include_router(foods_router)


@app.get("/health")
def health():
    return {"status": "ok"}
