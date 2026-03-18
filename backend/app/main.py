from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import models

app = FastAPI(
    title="CarroJusto API",
    description="Assistente de compra de carro para Portugal",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "CarroJusto"}


app.include_router(models.router)
