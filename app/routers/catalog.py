from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.catalog_visibility import hidden_catalog_ids
from app.services.markets import get_market_settings, list_market_settings
from app.services.offer_pricing import get_offer_prices, get_pack_prices

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/markets")
def markets(db: Session = Depends(get_db)) -> dict:
    return {"markets": list_market_settings(db)}


@router.get("/visibility")
def visibility(market: str = Query(default="ksa"), db: Session = Depends(get_db)) -> dict:
    try:
        market_settings = get_market_settings(db, market)
        hidden = hidden_catalog_ids(db, market)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not market_settings["active"]:
        hidden = {"product": set(), "pack": set()}

    return {
        "market": market_settings,
        "hidden_products": sorted(hidden["product"]),
        "hidden_packs": sorted(hidden["pack"]),
        "offer_prices": get_offer_prices(db, market_settings["code"]),
        "pack_prices": get_pack_prices(db, market_settings["code"]),
    }
