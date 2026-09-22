"""
CompareBuy — Catalog Router
Product listing, search, filter, and detail endpoints.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.models import Product, CatalogResponse, ProductCategory
from app.products import (
    get_all_products, get_product_by_id, search_products,
    get_unique_brands, get_unique_tags
)

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/products", response_model=CatalogResponse)
def list_products(
    search: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[int] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[int] = Query(None, ge=0, description="Maximum price"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    sort_by: Optional[str] = Query("score", description="Sort: score|price_asc|price_desc|name"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List all products with search, filter, and sort."""
    # Start with all or searched products
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
        tag_list = [t.strip().lower() for t in tags.split(",")]
        products = [
            p for p in products
            if any(tag in p.tags for tag in tag_list)
        ]

    # Sort
    if sort_by == "price_asc":
        products.sort(key=lambda p: p.price)
    elif sort_by == "price_desc":
        products.sort(key=lambda p: p.price, reverse=True)
    elif sort_by == "name":
        products.sort(key=lambda p: p.name)
    else:  # "score" — average of all score dimensions
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
def get_product(product_id: str):
    """Get a single product by ID."""
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/brands")
def list_brands():
    """Get all unique brands."""
    return {"brands": get_unique_brands()}


@router.get("/tags")
def list_tags():
    """Get all unique tags."""
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
