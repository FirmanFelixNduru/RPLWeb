"""
CompareBuy — Catalog Router
Product listing, search, filter, and detail endpoints with fail-closed production policy.
"""
import logging
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Literal, Optional
from sqlalchemy.orm import Session

from app.models import Product, CatalogResponse, ProductCategory
from app.db import get_db, is_fallback_allowed
from app.repositories import catalog_repo
from app.products import (
    get_all_products, get_product_by_id as get_fallback_product,
    search_products, get_unique_brands, get_unique_tags
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/products", response_model=CatalogResponse)
def list_products(
    search: Optional[str] = Query(None, description="Search query"),
    category: Optional[ProductCategory] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[int] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[int] = Query(None, ge=0, description="Maximum price"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    sort_by: Literal["score", "price_asc", "price_desc", "name"] = Query(
        "score", description="Sort: score|price_asc|price_desc|name"
    ),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Optional[Session] = Depends(get_db)
):
    """List all products with search, filter, and sort from DB or memory fallback."""
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=422,
            detail="min_price tidak boleh lebih besar dari max_price."
        )

    # Attempt PostgreSQL repository lookup if DB session is active
    if db is not None:
        try:
            products, total = catalog_repo.get_catalog_products(
                db=db,
                search=search,
                category=category,
                brand=brand,
                min_price=min_price,
                max_price=max_price,
                tags=tags,
                sort_by=sort_by,
                page=page,
                per_page=per_page
            )
            return CatalogResponse(
                products=products,
                total=total,
                page=page,
                per_page=per_page
            )
        except Exception as e:
            logger.error("Database query failed in list_products: %s", type(e).__name__)
            if not is_fallback_allowed():
                raise HTTPException(
                    status_code=503,
                    detail="Database service unavailable"
                ) from None

    if not is_fallback_allowed():
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable"
        )

    # Fallback to in-memory products (only in dev/test when explicitly permitted)
    if search:
        products = search_products(search)
    else:
        products = get_all_products()

    # Apply filters
    if category:
        products = [p for p in products if p.category.value == category]

    if brand:
        products = [p for p in products if p.brand.lower() == brand.lower()]

    if min_price is not None:
        products = [p for p in products if p.price >= min_price]

    if max_price is not None:
        products = [p for p in products if p.price <= max_price]

    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
        products = [
            p for p in products
            if any(tag.lower() in p.tags for tag in tag_list)
        ]

    # Sort
    if sort_by == "price_asc":
        products.sort(key=lambda p: p.price)
    elif sort_by == "price_desc":
        products.sort(key=lambda p: p.price, reverse=True)
    elif sort_by == "name":
        products.sort(key=lambda p: p.name)
    else:  # "score"
        products.sort(
            key=lambda p: (
                p.score_performance + p.score_camera + p.score_battery +
                p.score_display + p.score_build_quality + p.score_value +
                p.score_audio + p.score_software
            ) / 8,
            reverse=True
        )

    # Paginate
    total = len(products)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = products[start:end]

    return CatalogResponse(
        products=paginated,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/products/{product_id}", response_model=Product)
def get_product(product_id: str, db: Optional[Session] = Depends(get_db)):
    """Get a single product by ID."""
    if db is not None:
        try:
            product = catalog_repo.get_product_by_id(db, product_id)
            if product:
                return product
            if not is_fallback_allowed():
                raise HTTPException(status_code=404, detail="Product not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Database query failed in get_product for '%s': %s", product_id, type(e).__name__)
            if not is_fallback_allowed():
                raise HTTPException(
                    status_code=503,
                    detail="Database service unavailable"
                ) from None

    if not is_fallback_allowed():
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable"
        )

    # Fallback to in-memory (only when fallback is explicitly permitted)
    product = get_fallback_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/brands")
def list_brands(db: Optional[Session] = Depends(get_db)):
    """Get all unique brands."""
    if db is not None:
        try:
            brands = catalog_repo.get_all_brands(db)
            return {"brands": brands}
        except Exception as e:
            logger.error("Database query failed in list_brands: %s", type(e).__name__)
            if not is_fallback_allowed():
                raise HTTPException(
                    status_code=503,
                    detail="Database service unavailable"
                ) from None

    if not is_fallback_allowed():
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable"
        )

    return {"brands": get_unique_brands()}


@router.get("/tags")
def list_tags(db: Optional[Session] = Depends(get_db)):
    """Get all unique tags."""
    if db is not None:
        try:
            tags = catalog_repo.get_all_tags(db)
            return {"tags": tags}
        except Exception as e:
            logger.error("Database query failed in list_tags: %s", type(e).__name__)
            if not is_fallback_allowed():
                raise HTTPException(
                    status_code=503,
                    detail="Database service unavailable"
                ) from None

    if not is_fallback_allowed():
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable"
        )

    return {"tags": get_unique_tags()}


@router.get("/categories")
def list_categories():
    """Get all product categories."""
    return {
        "categories": [
            {"value": c.value, "label": c.value.replace("_", " ").title()}
            for c in ProductCategory
        ]
    }
