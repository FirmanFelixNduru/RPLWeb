"""
CompareBuy — Scoring Router
Wizard-based product scoring and recommendation.
"""
from fastapi import APIRouter

from app.models import WizardInput, ScoringResponse
from app.scoring import calculate_scores

router = APIRouter(prefix="/api", tags=["scoring"])


@router.post("/score", response_model=ScoringResponse)
def score_products(wizard_input: WizardInput):
    """
    Accept wizard preferences and return scored & ranked products.
    
    The scoring engine:
    1. Filters products by selected category
    2. Builds a weight vector from user priorities + scenario boosts
    3. Computes weighted scores per product
    4. Applies budget compliance modifiers
    5. Generates contextual "Why This Product?" narratives
    6. Returns results sorted by total score (descending)
    """
    return calculate_scores(wizard_input)
