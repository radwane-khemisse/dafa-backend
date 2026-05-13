from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers.admin import router as admin_router
from app.routers.analytics import router as analytics_router
from app.routers.catalog import router as catalog_router
from app.routers.health import router as health_router
from app.routers.orders import router as orders_router
from app.routers.tracking import router as tracking_router

settings = get_settings()

app = FastAPI(title="Dafa Kitchen API", version="1.0.0")

configured_origins = {
    origin.strip()
    for origin in (settings.cors_origins or "").split(",")
    if origin.strip()
}

allowed_origins = {
    "http://localhost:3000",
    "https://dafakitchen.shop",
    settings.frontend_url,
    *configured_origins,
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
app.include_router(analytics_router)
app.include_router(tracking_router)
app.include_router(catalog_router)
app.include_router(admin_router)
