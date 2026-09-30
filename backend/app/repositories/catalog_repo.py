"""
CompareBuy — Catalog Repository
Queries PostgreSQL for products, brands, tags, and detail models.
"""
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.entities import Product as ProductEntity, Brand, Tag, ProductSpecs, ReviewSentiment, WarrantyInfo, MarketplaceLink
from app.models import (
    Product as ProductModel,
    ProductSpecs as SpecsModel,
    ReviewSentiment as ReviewModel,
    WarrantyInfo as WarrantyModel,
    ProductCategory
)


def _entity_to_pydantic(entity: ProductEntity) -> ProductModel:
    """Map SQLAlchemy ProductEntity to Pydantic Product schema."""
    specs_data = entity.specs.specifications if entity.specs else {}
    specs = SpecsModel(**specs_data)

    review = ReviewModel(
        overall_score=entity.review_sentiment.overall_score if entity.review_sentiment else 4.5,
        total_reviews=entity.review_sentiment.total_reviews if entity.review_sentiment else 0,
        pros=entity.review_sentiment.pros if entity.review_sentiment else [],
        cons=entity.review_sentiment.cons if entity.review_sentiment else [],
        summary=entity.review_sentiment.summary if entity.review_sentiment else ""
    )

    warranty = WarrantyModel(
        duration_months=entity.warranty.duration_months if entity.warranty else 12,
        coverage=entity.warranty.coverage if entity.warranty else "",
        claim_ease=entity.warranty.claim_ease if entity.warranty else 7,
        official_service_centers=entity.warranty.official_service_centers if entity.warranty else 0,
        score=entity.warranty.score if entity.warranty else 0.0
    )

    links = {}
    if entity.marketplace_links:
        for ml in entity.marketplace_links:
            if ml.marketplace:
                links[ml.marketplace.code] = ml.url

    tags = [t.name for t in entity.tags] if entity.tags else []

    return ProductModel(
        id=entity.id,
        name=entity.name,
        brand=entity.brand.name if entity.brand else "",
        category=ProductCategory(entity.category),
        price=entity.price,
        image=entity.image_url or "",
        image_url=entity.image_url or "",
        description=entity.description or "",
        specs=specs,
        review_sentiment=review,
        warranty=warranty,
        marketplace_links=links,
        tags=tags,
        release_year=entity.release_year,
        score_performance=entity.score_performance,
        score_camera=entity.score_camera,
        score_battery=entity.score_battery,
        score_display=entity.score_display,
        score_build_quality=entity.score_build_quality,
        score_value=entity.score_value,
        score_audio=entity.score_audio,
        score_software=entity.score_software
    )


def get_catalog_products(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    tags: Optional[str] = None,
    sort_by: Optional[str] = "score",
    page: int = 1,
    per_page: int = 20
) -> tuple[list[ProductModel], int]:
    """Query catalog products from PostgreSQL with search, filtering, and sorting."""
    query = db.query(ProductEntity).filter(ProductEntity.is_active.is_(True))
    query = query.options(
        joinedload(ProductEntity.brand),
        joinedload(ProductEntity.specs),
        joinedload(ProductEntity.review_sentiment),
        joinedload(ProductEntity.warranty),
        joinedload(ProductEntity.tags),
        joinedload(ProductEntity.marketplace_links).joinedload(MarketplaceLink.marketplace)
    )

    if category:
        query = query.filter(ProductEntity.category == category)

    if brand:
        query = query.join(ProductEntity.brand).filter(Brand.name.ilike(brand))

    if min_price is not None:
        query = query.filter(ProductEntity.price >= min_price)

    if max_price is not None:
        query = query.filter(ProductEntity.price <= max_price)

    if search:
        search_term = f"%{search}%"
        query = query.join(ProductEntity.brand).filter(
            or_(
                ProductEntity.name.ilike(search_term),
                Brand.name.ilike(search_term),
                ProductEntity.description.ilike(search_term),
                ProductEntity.tags.any(Tag.name.ilike(search_term))
            )
        )

    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
        for tag_name in tag_list:
            query = query.filter(ProductEntity.tags.any(Tag.name.ilike(tag_name)))

    entities = query.all()
    models = [_entity_to_pydantic(e) for e in entities]

    # Sort
    if sort_by == "price_asc":
        models.sort(key=lambda p: p.price)
    elif sort_by == "price_desc":
        models.sort(key=lambda p: p.price, reverse=True)
    elif sort_by == "name":
        models.sort(key=lambda p: p.name)
    else:  # "score"
        models.sort(
            key=lambda p: (
                p.score_performance + p.score_camera + p.score_battery +
                p.score_display + p.score_build_quality + p.score_value +
                p.score_audio + p.score_software
            ) / 8,
            reverse=True
        )

    total = len(models)
    start = (page - 1) * per_page
    paginated = models[start:start + per_page]

    return paginated, total


def get_product_by_id(db: Session, product_id: str) -> Optional[ProductModel]:
    """Retrieve single product from database by ID."""
    entity = db.query(ProductEntity).filter(
        ProductEntity.id == product_id,
        ProductEntity.is_active.is_(True)
    ).options(
        joinedload(ProductEntity.brand),
        joinedload(ProductEntity.specs),
        joinedload(ProductEntity.review_sentiment),
        joinedload(ProductEntity.warranty),
        joinedload(ProductEntity.tags),
        joinedload(ProductEntity.marketplace_links).joinedload(MarketplaceLink.marketplace)
    ).first()

    if not entity:
        return None
    return _entity_to_pydantic(entity)


def get_all_brands(db: Session) -> list[str]:
    """Return all unique brand names in PostgreSQL."""
    brands = db.query(Brand.name).distinct().order_by(Brand.name).all()
    return [b[0] for b in brands]


def get_all_tags(db: Session) -> list[str]:
    """Return all unique tag names in PostgreSQL."""
    tags = db.query(Tag.name).distinct().order_by(Tag.name).all()
    return [t[0] for t in tags]
