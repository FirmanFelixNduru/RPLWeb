"""
CompareBuy — SQLAlchemy Database Entities
Implements all 10 persistent domain models specified in requirement-revisi.md.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, BigInteger, Float, Boolean,
    DateTime, ForeignKey, Text, JSON, CheckConstraint,
    UniqueConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db import Base

JSON_VALUE = JSON().with_variant(JSONB, "postgresql")


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())

    products = relationship("Product", back_populates="brand", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_brand_name_nonempty"),
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    price = Column(BigInteger, nullable=False, index=True)
    image_url = Column(Text, default="")
    description = Column(Text, default="")
    release_year = Column(Integer, default=2024, nullable=False)

    score_performance = Column(Integer, default=50, nullable=False)
    score_camera = Column(Integer, default=50, nullable=False)
    score_battery = Column(Integer, default=50, nullable=False)
    score_display = Column(Integer, default=50, nullable=False)
    score_build_quality = Column(Integer, default=50, nullable=False)
    score_value = Column(Integer, default=50, nullable=False)
    score_audio = Column(Integer, default=50, nullable=False)
    score_software = Column(Integer, default=50, nullable=False)

    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_product_price_non_negative"),
        CheckConstraint("release_year >= 1900", name="ck_product_release_year_valid"),
        CheckConstraint("length(trim(name)) > 0", name="ck_product_name_nonempty"),
        CheckConstraint(
            "category IN ('smartphone', 'laptop', 'tablet', 'tws', 'smartwatch')",
            name="ck_product_category_valid"
        ),
        CheckConstraint("score_performance >= 0 AND score_performance <= 100", name="ck_product_score_perf"),
        CheckConstraint("score_camera >= 0 AND score_camera <= 100", name="ck_product_score_cam"),
        CheckConstraint("score_battery >= 0 AND score_battery <= 100", name="ck_product_score_batt"),
        CheckConstraint("score_display >= 0 AND score_display <= 100", name="ck_product_score_disp"),
        CheckConstraint("score_build_quality >= 0 AND score_build_quality <= 100", name="ck_product_score_build"),
        CheckConstraint("score_value >= 0 AND score_value <= 100", name="ck_product_score_val"),
        CheckConstraint("score_audio >= 0 AND score_audio <= 100", name="ck_product_score_aud"),
        CheckConstraint("score_software >= 0 AND score_software <= 100", name="ck_product_score_soft"),
    )

    brand = relationship("Brand", back_populates="products")
    specs = relationship("ProductSpecs", uselist=False, back_populates="product", cascade="all, delete-orphan")
    review_sentiment = relationship("ReviewSentiment", uselist=False, back_populates="product", cascade="all, delete-orphan")
    warranty = relationship("WarrantyInfo", uselist=False, back_populates="product", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="product_tags", back_populates="products")
    marketplace_links = relationship("MarketplaceLink", back_populates="product", cascade="all, delete-orphan")
    marketplace_prices = relationship("MarketplacePrice", back_populates="product", cascade="all, delete-orphan")


class ProductSpecs(Base):
    __tablename__ = "product_specs"

    product_id = Column(String(50), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    specifications = Column(JSON_VALUE, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    product = relationship("Product", back_populates="specs")


class ReviewSentiment(Base):
    __tablename__ = "review_sentiments"

    product_id = Column(String(50), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    overall_score = Column(Float, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    pros = Column(JSON_VALUE, default=list, nullable=False)
    cons = Column(JSON_VALUE, default=list, nullable=False)
    summary = Column(Text, default="", nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        CheckConstraint("overall_score >= 0.0 AND overall_score <= 5.0", name="ck_review_overall_score"),
        CheckConstraint("total_reviews >= 0", name="ck_review_total_reviews"),
    )

    product = relationship("Product", back_populates="review_sentiment")


class WarrantyInfo(Base):
    __tablename__ = "warranty_infos"

    product_id = Column(String(50), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    duration_months = Column(Integer, default=12, nullable=False)
    coverage = Column(Text, default="", nullable=False)
    claim_ease = Column(Integer, default=7, nullable=False)
    official_service_centers = Column(Integer, default=0, nullable=False)
    score = Column(Float, default=0.0, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        CheckConstraint("duration_months >= 0", name="ck_warranty_duration_months"),
        CheckConstraint("claim_ease >= 1 AND claim_ease <= 10", name="ck_warranty_claim_ease"),
        CheckConstraint("official_service_centers >= 0", name="ck_warranty_service_centers"),
        CheckConstraint("score >= 0.0 AND score <= 100.0", name="ck_warranty_score_range"),
    )

    product = relationship("Product", back_populates="warranty")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    products = relationship("Product", secondary="product_tags", back_populates="tags")


class ProductTag(Base):
    __tablename__ = "product_tags"

    product_id = Column(String(50), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_tag_name_nonempty"),
        Index("ix_product_tag_pair", "product_id", "tag_id"),
    )


class Marketplace(Base):
    __tablename__ = "marketplaces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)

    links = relationship("MarketplaceLink", back_populates="marketplace", cascade="all, delete-orphan")
    prices = relationship("MarketplacePrice", back_populates="marketplace", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("length(trim(code)) > 0", name="ck_marketplace_code_nonempty"),
    )


class MarketplaceLink(Base):
    __tablename__ = "marketplace_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    marketplace_id = Column(Integer, ForeignKey("marketplaces.id", ondelete="CASCADE"), nullable=False)
    url = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("product_id", "marketplace_id", name="uq_product_marketplace_link"),
        CheckConstraint(
            "url LIKE 'http://%' OR url LIKE 'https://%'",
            name="ck_marketplace_link_http_url"
        ),
    )

    product = relationship("Product", back_populates="marketplace_links")
    marketplace = relationship("Marketplace", back_populates="links")


class MarketplacePrice(Base):
    __tablename__ = "marketplace_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    marketplace_id = Column(Integer, ForeignKey("marketplaces.id", ondelete="CASCADE"), nullable=False)
    price = Column(BigInteger, nullable=False)
    seller = Column(String(255), default="")
    url = Column(Text, nullable=False)
    available = Column(Boolean, default=True, nullable=False)
    source = Column(String(20), nullable=False, default="fallback")  # "scraped" or "fallback"
    captured_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("price > 0", name="ck_marketplace_price_positive"),
        CheckConstraint("source IN ('scraped', 'fallback')", name="ck_marketplace_price_source"),
        CheckConstraint(
            "url LIKE 'http://%' OR url LIKE 'https://%'",
            name="ck_marketplace_price_http_url"
        ),
        Index("ix_product_mkt_captured", "product_id", "marketplace_id", "captured_at"),
    )

    product = relationship("Product", back_populates="marketplace_prices")
    marketplace = relationship("Marketplace", back_populates="prices")
