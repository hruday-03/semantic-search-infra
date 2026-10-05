from fastapi import FastAPI

from app.api.routes import router

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}

app.include_router(router)