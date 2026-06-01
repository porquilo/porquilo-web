from fastapi import FastAPI

app = FastAPI(title="Porquilo")


@app.get("/health")
def health():
    return {"status": "ok"}
