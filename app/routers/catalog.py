from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.catalog_visibility import hidden_catalog_ids

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/visibility")
def visibility(db: Session = Depends(get_db)) -> dict:
    hidden = hidden_catalog_ids(db)
    return {
        "hidden_products": sorted(hidden["product"]),
        "hidden_packs": sorted(hidden["pack"]),
    }
