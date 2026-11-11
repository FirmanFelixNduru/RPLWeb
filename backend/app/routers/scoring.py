"""
CompareBuy — Scoring Router
Wizard-based product scoring and recommendation.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models import WizardInput, ScoringResponse
from app.scoring import calculate_scores
from app.db import get_db, is_fallback_allowed
from app.repositories import catalog_repo
from app.products import get_products_by_category as get_fallback_products_by_category

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["scoring"])


@router.post("/score", response_model=ScoringResponse)
def score_products(
    wizard_input: WizardInput,
    db: Optional[Session] = Depends(get_db)
) -> ScoringResponse:
    """
    Accept wizard preferences and return scored & ranked products.
    Authoritative candidate products come from PostgreSQL in production.

    The scoring engine:
    1. Filters active products by selected category from PostgreSQL
    2. Builds a weight vector from user priorities + scenario boosts
    3. Computes weighted scores per product
    4. Applies budget compliance modifiers
    5. Generates contextual "Why This Product?" narratives
    6. Returns results sorted by total score (descending)
    """
    category_str = wizard_input.category.value if hasattr(wizard_input.category, "value") else str(wizard_input.category)

    if db is not None:
        try:
            db_products = catalog_repo.get_products_by_category(db, category_str)
            return calculate_scores(wizard_input, products=db_products)
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error("Database query failed in score_products: %s", type(e).__name__)
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

    # Fallback to in-memory catalog (strictly in dev/test when DB outage occurs and explicitly permitted)
    fallback_products = get_fallback_products_by_category(category_str)
    return calculate_scores(wizard_input, products=fallback_products)
