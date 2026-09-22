"""
CompareBuy Backend — Pydantic Models & Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────
class ProductCategory(str, Enum):
    SMARTPHONE = "smartphone"
    LAPTOP = "laptop"
    TABLET = "tablet"
    TWS = "tws"
    SMARTWATCH = "smartwatch"


class UsageScenario(str, Enum):
    GAMING = "gaming"
    PRODUCTIVITY = "productivity"
    PHOTOGRAPHY = "photography"
    SOCIAL_MEDIA = "social_media"
    CONTENT_CREATION = "content_creation"
    BUSINESS = "business"
    STUDENT = "student"
    FITNESS = "fitness"
    MULTIMEDIA = "multimedia"
    CASUAL = "casual"


# ──────────────────────────────────────────────
# Product Models
# ──────────────────────────────────────────────
class WarrantyInfo(BaseModel):
    duration_months: int = Field(..., description="Warranty duration in months")
    coverage: str = Field(..., description="What the warranty covers")
    claim_ease: int = Field(..., ge=1, le=10, description="Ease of claim 1-10")
    official_service_centers: int = Field(default=0, description="Number of service centers")
    score: float = Field(default=0.0, description="Computed warranty index 0-100")


class ReviewSentiment(BaseModel):
    overall_score: float = Field(..., ge=0, le=5, description="Overall rating 0-5")
    total_reviews: int = Field(default=0)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    summary: str = Field(default="")


class MarketplacePrice(BaseModel):
    marketplace: str
    price: int
    url: str
    seller: str = ""
    available: bool = True


class ProductSpecs(BaseModel):
    """Flexible spec container — keys vary by category."""
    display: Optional[str] = None
    processor: Optional[str] = None
    ram: Optional[str] = None
    storage: Optional[str] = None
    battery: Optional[str] = None
    camera: Optional[str] = None
    os: Optional[str] = None
    weight: Optional[str] = None
    connectivity: Optional[str] = None
    screen_size: Optional[str] = None
    refresh_rate: Optional[str] = None
    resolution: Optional[str] = None
    gpu: Optional[str] = None
    water_resistance: Optional[str] = None
    driver_size: Optional[str] = None
    anc: Optional[str] = None
    codec: Optional[str] = None
    sensors: Optional[str] = None
    build_material: Optional[str] = None
    special_features: Optional[str] = None


class Product(BaseModel):
    id: str
    name: str
    brand: str
    category: ProductCategory
    price: int = Field(..., description="Base MSRP price in IDR")
    image: str = Field(default="")
    description: str = Field(default="")
    specs: ProductSpecs
    review_sentiment: ReviewSentiment
    warranty: WarrantyInfo
    marketplace_links: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    release_year: int = Field(default=2024)

    # Numeric performance scores (0-100) used by scoring engine
    score_performance: int = Field(default=50)
    score_camera: int = Field(default=50)
    score_battery: int = Field(default=50)
    score_display: int = Field(default=50)
    score_build_quality: int = Field(default=50)
    score_value: int = Field(default=50)
    score_audio: int = Field(default=50)
    score_software: int = Field(default=50)


# ──────────────────────────────────────────────
# Wizard / Scoring Models
# ──────────────────────────────────────────────
class WizardInput(BaseModel):
    category: ProductCategory
    budget_min: int = Field(..., ge=0)
    budget_max: int = Field(..., ge=0)
    scenarios: list[UsageScenario] = Field(default_factory=list)
    priorities: dict[str, int] = Field(
        default_factory=dict,
        description="Priority weights: performance, camera, battery, display, build_quality, value, audio, software (1-5)"
    )


class ScoreBreakdown(BaseModel):
    dimension: str
    weight: float
    raw_score: int
    weighted_score: float


class ScoredProduct(BaseModel):
    product: Product
    total_score: float
    rank: int
    score_breakdown: list[ScoreBreakdown]
    why_this_product: str
    budget_fit: str  # "within", "below", "above"


class ScoringResponse(BaseModel):
    results: list[ScoredProduct]
    total_products_evaluated: int
    wizard_input: WizardInput


# ──────────────────────────────────────────────
# Comparison Models
# ──────────────────────────────────────────────
class CompareRequest(BaseModel):
    product_ids: list[str] = Field(..., min_length=2, max_length=4)


class SpecHighlight(BaseModel):
    spec_name: str
    values: dict[str, str]  # product_id → value
    best_product_id: str


class CompareResponse(BaseModel):
    products: list[Product]
    highlights: list[SpecHighlight]


# ──────────────────────────────────────────────
# Catalog Query Models
# ──────────────────────────────────────────────
class CatalogQuery(BaseModel):
    search: Optional[str] = None
    category: Optional[ProductCategory] = None
    brand: Optional[str] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    tags: Optional[list[str]] = None
    sort_by: Optional[str] = "score"  # score | price_asc | price_desc | name
    page: int = 1
    per_page: int = 20


class CatalogResponse(BaseModel):
    products: list[Product]
    total: int
    page: int
    per_page: int


# ──────────────────────────────────────────────
# Price Scraping Models
# ──────────────────────────────────────────────
class PriceResponse(BaseModel):
    product_id: str
    product_name: str
    prices: list[MarketplacePrice]
    last_updated: str
