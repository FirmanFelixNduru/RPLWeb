"""
CompareBuy — Price Router
Live marketplace price fetching.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from sqlalchemy.orm import Session

from app.products import get_product_by_id as get_fallback_product
from app.db import get_db
from app.repositories import catalog_repo
from app.scraper import get_live_prices

router = APIRouter(prefix="/api", tags=["prices"])


@router.get("/prices/{product_id}")
async def fetch_prices(product_id: str, db: Optional[Session] = Depends(get_db)):
    """
    Fetch live marketplace prices for a product.
    Attempts real scraping from Tokopedia, Shopee, and Lazada.
    Falls back to cached/realistic prices if scraping fails.
    """
    product = None
    if db is not None:
        try:
            product = catalog_repo.get_product_by_id(db, product_id)
        except Exception:
            pass

    if not product:
        product = get_fallback_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await get_live_prices(product_id, product.name)
    return result
