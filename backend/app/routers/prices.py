"""
CompareBuy — Price Router
Live marketplace price fetching.
"""
from fastapi import APIRouter, HTTPException

from app.products import get_product_by_id
from app.scraper import get_live_prices

router = APIRouter(prefix="/api", tags=["prices"])


@router.get("/prices/{product_id}")
async def fetch_prices(product_id: str):
    """
    Fetch live marketplace prices for a product.
    Attempts real scraping from Tokopedia, Shopee, and Lazada.
    Falls back to cached/realistic prices if scraping fails.
    """
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await get_live_prices(product_id, product.name)
    return result
