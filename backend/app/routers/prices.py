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
from app.price_service import price_cache
from app.scrape_worker import ScrapeOverloadError, ScrapeTimeoutError

router = APIRouter(prefix="/api", tags=["prices"])


def get_price_product_name(product_id: str, db: Optional[Session] = Depends(get_db)) -> str:
    """Run DB lookup in FastAPI's worker pool and release it before external I/O."""
    product = None
    if db is not None:
        try:
            product = catalog_repo.get_product_by_id(db, product_id)
        except Exception:
            pass
        finally:
            db.close()

    if not product:
        product = get_fallback_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product.name


@router.get("/prices/{product_id}")
async def fetch_prices(product_id: str, product_name: str = Depends(get_price_product_name)):
    """Fetch marketplace prices, sharing valid cached results for 300 seconds."""
    try:
        return await price_cache.get(product_id, product_name)
    except ScrapeOverloadError:
        raise HTTPException(status_code=503, detail="Marketplace price lookup busy") from None
    except ScrapeTimeoutError:
        raise HTTPException(status_code=504, detail="Marketplace price lookup timed out") from None
