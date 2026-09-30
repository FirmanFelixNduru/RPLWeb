"""
CompareBuy — Repeatable Database Seeder
Seeds PostgreSQL from the curated 20-product catalog in app/products.py.
Idempotent: safe to run multiple times without creating duplicates.
"""
import os
import sys
from datetime import datetime, timezone

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import engine, SessionLocal, Base
from app.entities import (
    Brand, Product, ProductSpecs, ReviewSentiment,
    WarrantyInfo, Tag, ProductTag, Marketplace,
    MarketplaceLink, MarketplacePrice
)
from app.products import PRODUCTS


def seed_database():
    """Seed the database idempotently with curated products."""
    if engine is None or SessionLocal is None:
        print("[ERROR] DATABASE_URL is not set or database engine is not initialized.")
        print("Please check your .env configuration.")
        return False

    print("[INFO] Initializing database schema...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print(f"[SEED] Seeding {len(PRODUCTS)} curated products from app/products.py...")

        # 1. Ensure standard Marketplaces exist
        marketplaces_data = [
            ("tokopedia", "Tokopedia"),
            ("shopee", "Shopee"),
            ("lazada", "Lazada"),
        ]
        marketplace_map = {}
        for code, name in marketplaces_data:
            mkt = db.query(Marketplace).filter(Marketplace.code == code).first()
            if not mkt:
                mkt = Marketplace(code=code, name=name)
                db.add(mkt)
                db.flush()
            marketplace_map[code] = mkt

        for p in PRODUCTS:
            # 2. Brand (idempotent)
            brand_entity = db.query(Brand).filter(Brand.name == p.brand).first()
            if not brand_entity:
                brand_entity = Brand(name=p.brand)
                db.add(brand_entity)
                db.flush()

            # 3. Product (idempotent)
            product_entity = db.query(Product).filter(Product.id == p.id).first()
            if not product_entity:
                product_entity = Product(
                    id=p.id,
                    name=p.name,
                    brand_id=brand_entity.id,
                    category=p.category.value,
                    price=p.price,
                    image_url=p.image or p.image_url,
                    description=p.description,
                    release_year=p.release_year,
                    score_performance=p.score_performance,
                    score_camera=p.score_camera,
                    score_battery=p.score_battery,
                    score_display=p.score_display,
                    score_build_quality=p.score_build_quality,
                    score_value=p.score_value,
                    score_audio=p.score_audio,
                    score_software=p.score_software,
                    is_active=True
                )
                db.add(product_entity)
                db.flush()
            else:
                # Update existing fields
                product_entity.name = p.name
                product_entity.brand_id = brand_entity.id
                product_entity.category = p.category.value
                product_entity.price = p.price
                product_entity.image_url = p.image or p.image_url
                product_entity.description = p.description
                product_entity.release_year = p.release_year
                product_entity.score_performance = p.score_performance
                product_entity.score_camera = p.score_camera
                product_entity.score_battery = p.score_battery
                product_entity.score_display = p.score_display
                product_entity.score_build_quality = p.score_build_quality
                product_entity.score_value = p.score_value
                product_entity.score_audio = p.score_audio
                product_entity.score_software = p.score_software
                db.flush()

            # 4. ProductSpecs (idempotent)
            specs_data = p.specs.model_dump(exclude_none=True)
            specs_entity = db.query(ProductSpecs).filter(ProductSpecs.product_id == p.id).first()
            if not specs_entity:
                specs_entity = ProductSpecs(
                    product_id=p.id,
                    specifications=specs_data
                )
                db.add(specs_entity)
            else:
                specs_entity.specifications = specs_data

            # 5. ReviewSentiment (idempotent)
            review_entity = db.query(ReviewSentiment).filter(ReviewSentiment.product_id == p.id).first()
            if not review_entity:
                review_entity = ReviewSentiment(
                    product_id=p.id,
                    overall_score=p.review_sentiment.overall_score,
                    total_reviews=p.review_sentiment.total_reviews,
                    pros=p.review_sentiment.pros,
                    cons=p.review_sentiment.cons,
                    summary=p.review_sentiment.summary
                )
                db.add(review_entity)
            else:
                review_entity.overall_score = p.review_sentiment.overall_score
                review_entity.total_reviews = p.review_sentiment.total_reviews
                review_entity.pros = p.review_sentiment.pros
                review_entity.cons = p.review_sentiment.cons
                review_entity.summary = p.review_sentiment.summary

            # 6. WarrantyInfo (idempotent)
            warranty_entity = db.query(WarrantyInfo).filter(WarrantyInfo.product_id == p.id).first()
            if not warranty_entity:
                warranty_entity = WarrantyInfo(
                    product_id=p.id,
                    duration_months=p.warranty.duration_months,
                    coverage=p.warranty.coverage,
                    claim_ease=p.warranty.claim_ease,
                    official_service_centers=p.warranty.official_service_centers,
                    score=p.warranty.score
                )
                db.add(warranty_entity)
            else:
                warranty_entity.duration_months = p.warranty.duration_months
                warranty_entity.coverage = p.warranty.coverage
                warranty_entity.claim_ease = p.warranty.claim_ease
                warranty_entity.official_service_centers = p.warranty.official_service_centers
                warranty_entity.score = p.warranty.score

            # 7. Tags & ProductTag (idempotent)
            for tag_name in p.tags:
                tag_name_clean = tag_name.strip()
                tag_entity = db.query(Tag).filter(Tag.name == tag_name_clean).first()
                if not tag_entity:
                    tag_entity = Tag(name=tag_name_clean)
                    db.add(tag_entity)
                    db.flush()

                pt_link = db.query(ProductTag).filter(
                    ProductTag.product_id == p.id,
                    ProductTag.tag_id == tag_entity.id
                ).first()
                if not pt_link:
                    pt_link = ProductTag(product_id=p.id, tag_id=tag_entity.id)
                    db.add(pt_link)

            # 8. Marketplace Links & initial Prices (idempotent)
            for mkt_code, mkt_url in p.marketplace_links.items():
                mkt_obj = marketplace_map.get(mkt_code.lower())
                if mkt_obj:
                    link_entity = db.query(MarketplaceLink).filter(
                        MarketplaceLink.product_id == p.id,
                        MarketplaceLink.marketplace_id == mkt_obj.id
                    ).first()
                    if not link_entity:
                        link_entity = MarketplaceLink(
                            product_id=p.id,
                            marketplace_id=mkt_obj.id,
                            url=mkt_url
                        )
                        db.add(link_entity)

                    # Initial baseline fallback snapshot if no price exists
                    existing_price = db.query(MarketplacePrice).filter(
                        MarketplacePrice.product_id == p.id,
                        MarketplacePrice.marketplace_id == mkt_obj.id
                    ).first()
                    if not existing_price:
                        price_snapshot = MarketplacePrice(
                            product_id=p.id,
                            marketplace_id=mkt_obj.id,
                            price=p.price,
                            seller=f"{p.brand} Official Store",
                            url=mkt_url,
                            available=True,
                            source="fallback",
                            captured_at=datetime.now(timezone.utc)
                        )
                        db.add(price_snapshot)

        db.commit()
        print("[SUCCESS] Database seeding completed successfully without duplicates!")
        return True
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error during database seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
