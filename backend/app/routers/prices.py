"""
CompareBuy — Price Router
Live marketplace price fetching.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.products import get_product_by_id as get_fallback_product
from app.db import get_db, is_fallback_allowed
from app.repositories import catalog_repo
from app.price_service import price_cache
from app.scrape_worker import ScrapeOverloadError, ScrapeTimeoutError
from app.security import check_price_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["prices"])


def get_price_product_name(product_id: str, db: Optional[Session] = Depends(get_db)) -> str:
    """Run DB lookup in FastAPI's worker pool and release it before external I/O."""
    if db is not None:
        try:
            product = catalog_repo.get_product_by_id(db, product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            return product.name
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error("Database query failed in get_price_product_name for '%s': %s", product_id, type(e).__name__)
            if not is_fallback_allowed():
                raise HTTPException(
                    status_code=503,
                    detail="Database service unavailable"
                ) from None
        finally:
            try:
                db.close()
            except Exception:
                pass

    if not is_fallback_allowed():
        raise HTTPException(status_code=503, detail="Database service unavailable")

    # Fallback to in-memory catalog (only in dev/test for DB outages when explicitly permitted)
    product = get_fallback_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product.name


@router.get("/prices/{product_id}", dependencies=[Depends(check_price_rate_limit)])
async def fetch_prices(product_id: str, product_name: str = Depends(get_price_product_name)):
    """Fetch marketplace prices, sharing valid cached results for 300 seconds."""
    try:
        return await price_cache.get(product_id, product_name)
    except ScrapeOverloadError:
        raise HTTPException(status_code=503, detail="Marketplace price lookup busy") from None
    except ScrapeTimeoutError:
        raise HTTPException(status_code=504, detail="Marketplace price lookup timed out") from None
