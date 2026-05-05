from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    api_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    database_url: str = "postgresql+psycopg://dafakitchen:dafakitchen@localhost:5432/dafa_kitchen"

    order_webhook_url: str | None = None
    order_webhook_secret: str | None = None

    meta_pixel_id: str | None = None
    meta_access_token: str | None = None
    meta_graph_version: str = "v22.0"
    meta_test_event_code: str | None = None

    tiktok_pixel_code: str | None = None
    tiktok_access_token: str | None = None
    tiktok_events_api_url: str = "https://business-api.tiktok.com/open_api/v1.3/event/track/"
    tiktok_test_event_code: str | None = None
    tiktok_phone_hash_mode: str = Field(default="e164", pattern="^(e164|digits)$")

    snap_pixel_id: str | None = None
    snap_access_token: str | None = None

    enable_capi: bool = True
    enable_sheets_webhook: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()

