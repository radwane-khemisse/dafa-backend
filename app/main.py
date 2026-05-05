from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers.health import router as health_router
from app.routers.orders import router as orders_router

settings = get_settings()

app = FastAPI(title="Dafa Kitchen API", version="1.0.0")

allowed_origins = {
    "http://localhost:3000",
    "https://dafakitchen.shop",
    settings.frontend_url,
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(orders_router)

