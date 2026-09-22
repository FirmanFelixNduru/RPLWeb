"""
CompareBuy — Weighted Dynamic Scoring Engine
Multi-Criteria Decision Analysis (MCDA) with user-weighted preferences.
"""
from app.models import (
    WizardInput, ScoredProduct, ScoringResponse,
    ScoreBreakdown, Product, UsageScenario
)
from app.products import get_all_products, get_products_by_category


# ──────────────────────────────────────────────
# Scenario → Dimension Weight Boosts
# ──────────────────────────────────────────────
SCENARIO_BOOSTS: dict[str, dict[str, float]] = {
    "gaming": {"performance": 0.15, "display": 0.08, "audio": 0.05, "battery": 0.02},
    "productivity": {"performance": 0.08, "software": 0.10, "display": 0.05, "battery": 0.07},
    "photography": {"camera": 0.20, "display": 0.05, "software": 0.03},
    "social_media": {"camera": 0.10, "display": 0.05, "battery": 0.05},
    "content_creation": {"performance": 0.10, "display": 0.10, "camera": 0.05, "software": 0.05},
    "business": {"software": 0.10, "build_quality": 0.08, "battery": 0.07, "performance": 0.05},
    "student": {"value": 0.15, "battery": 0.10, "software": 0.05},
    "fitness": {"build_quality": 0.10, "battery": 0.10, "software": 0.05},
    "multimedia": {"display": 0.12, "audio": 0.12, "battery": 0.06},
    "casual": {"value": 0.10, "battery": 0.08, "build_quality": 0.05, "software": 0.05},
}

# All scoring dimensions
DIMENSIONS = [
    "performance", "camera", "battery", "display",
    "build_quality", "value", "audio", "software"
]

# Human-readable labels (Indonesian)
DIMENSION_LABELS = {
    "performance": "Performa",
    "camera": "Kamera",
    "battery": "Baterai",
    "display": "Layar",
    "build_quality": "Build Quality",
    "value": "Value for Money",
    "audio": "Audio",
    "software": "Software & Update",
}


def _get_product_score(product: Product, dimension: str) -> int:
    """Get a product's raw score (0-100) for a given dimension."""
    score_map = {
        "performance": product.score_performance,
        "camera": product.score_camera,
        "battery": product.score_battery,
        "display": product.score_display,
        "build_quality": product.score_build_quality,
        "value": product.score_value,
        "audio": product.score_audio,
        "software": product.score_software,
    }
    return score_map.get(dimension, 50)


def _build_weight_vector(wizard: WizardInput) -> dict[str, float]:
    """
    Build normalized weight vector from:
    1. User's explicit priority sliders (1-5)
    2. Usage scenario boosts
    """
    # Start with user priorities (default to 3 if not set)
    raw_weights: dict[str, float] = {}
    for dim in DIMENSIONS:
        raw_weights[dim] = float(wizard.priorities.get(dim, 3))

    # Apply scenario boosts
    for scenario in wizard.scenarios:
        boosts = SCENARIO_BOOSTS.get(scenario.value, {})
        for dim, boost in boosts.items():
            raw_weights[dim] = raw_weights.get(dim, 3.0) + boost * 10  # scale boost

    # Normalize to sum = 1.0
    total = sum(raw_weights.values())
    if total == 0:
        total = 1.0
    weights = {dim: w / total for dim, w in raw_weights.items()}
    return weights


def _budget_fit_label(price: int, budget_min: int, budget_max: int) -> str:
    """Determine if a product fits the user's budget."""
    if budget_min <= price <= budget_max:
        return "within"
    elif price < budget_min:
        return "below"
    else:
        return "above"


def _budget_modifier(price: int, budget_min: int, budget_max: int) -> float:
    """
    Budget compliance modifier:
    - Within budget: +5 bonus
    - Below budget: +2 bonus (under budget is okay)
    - Above budget by <20%: -5 penalty
    - Above budget by >20%: -15 penalty
    """
    if budget_min <= price <= budget_max:
        return 5.0
    elif price < budget_min:
        return 2.0
    else:
        over_pct = (price - budget_max) / max(budget_max, 1)
        if over_pct <= 0.2:
            return -5.0
        else:
            return -15.0


def _generate_why_narrative(
    product: Product,
    breakdown: list[ScoreBreakdown],
    budget_fit: str,
    wizard: WizardInput
) -> str:
    """Generate contextual 'Why This Product?' narrative in Indonesian."""
    # Find top 3 scoring dimensions
    sorted_dims = sorted(breakdown, key=lambda b: b.weighted_score, reverse=True)
    top_dims = sorted_dims[:3]

    parts = []

    # Opening
    parts.append(f"{product.name} mendapatkan skor tinggi karena:")

    # Top strengths
    for i, dim in enumerate(top_dims, 1):
        label = DIMENSION_LABELS.get(dim.dimension, dim.dimension)
        raw = dim.raw_score
        if raw >= 90:
            desc = "luar biasa"
        elif raw >= 80:
            desc = "sangat baik"
        elif raw >= 70:
            desc = "baik"
        else:
            desc = "cukup memadai"
        parts.append(f"  {i}. **{label}** yang {desc} (skor {raw}/100)")

    # Budget context
    if budget_fit == "within":
        parts.append(f"\n💰 Produk ini **sesuai dengan budget** Anda (Rp {wizard.budget_min:,} — Rp {wizard.budget_max:,}).")
    elif budget_fit == "below":
        parts.append(f"\n💰 Produk ini **di bawah budget** Anda — hemat lebih banyak!")
    else:
        parts.append(f"\n⚠️ Produk ini **di atas budget** Anda, namun menawarkan value yang sebanding.")

    # Scenario match
    if wizard.scenarios:
        scenario_labels = {
            "gaming": "gaming",
            "productivity": "produktivitas",
            "photography": "fotografi",
            "social_media": "media sosial",
            "content_creation": "kreasi konten",
            "business": "bisnis",
            "student": "kebutuhan mahasiswa",
            "fitness": "fitness & olahraga",
            "multimedia": "multimedia & hiburan",
            "casual": "penggunaan kasual",
        }
        matched = [scenario_labels.get(s.value, s.value) for s in wizard.scenarios]
        parts.append(f"\n🎯 Sangat cocok untuk skenario: {', '.join(matched)}.")

    # Warranty highlight
    if product.warranty.score >= 85:
        parts.append(f"\n🛡️ Dukungan purna jual **excellent** — garansi {product.warranty.duration_months} bulan dengan kemudahan klaim tinggi.")
    elif product.warranty.score >= 70:
        parts.append(f"\n🛡️ Dukungan purna jual **baik** — garansi {product.warranty.duration_months} bulan.")

    return "\n".join(parts)


def calculate_scores(wizard: WizardInput) -> ScoringResponse:
    """
    Main scoring engine entry point.
    1. Filter products by category
    2. Build weight vector from user preferences
    3. Score each product
    4. Apply budget modifier
    5. Generate narratives
    6. Return ranked results
    """
    # 1. Get products in the selected category
    products = get_products_by_category(wizard.category.value)

    if not products:
        return ScoringResponse(
            results=[],
            total_products_evaluated=0,
            wizard_input=wizard
        )

    # 2. Build weight vector
    weights = _build_weight_vector(wizard)

    # 3. Score each product
    scored_list: list[ScoredProduct] = []

    for product in products:
        breakdown: list[ScoreBreakdown] = []
        total_weighted = 0.0

        for dim in DIMENSIONS:
            raw = _get_product_score(product, dim)
            w = weights.get(dim, 0.0)
            ws = raw * w
            total_weighted += ws
            breakdown.append(ScoreBreakdown(
                dimension=dim,
                weight=round(w, 4),
                raw_score=raw,
                weighted_score=round(ws, 2)
            ))

        # 4. Budget modifier
        budget_fit = _budget_fit_label(product.price, wizard.budget_min, wizard.budget_max)
        modifier = _budget_modifier(product.price, wizard.budget_min, wizard.budget_max)
        total_score = round(total_weighted + modifier, 2)

        # 5. Generate narrative
        why = _generate_why_narrative(product, breakdown, budget_fit, wizard)

        scored_list.append(ScoredProduct(
            product=product,
            total_score=total_score,
            rank=0,  # assigned below
            score_breakdown=breakdown,
            why_this_product=why,
            budget_fit=budget_fit
        ))

    # 6. Rank by total score descending
    scored_list.sort(key=lambda x: x.total_score, reverse=True)
    for i, sp in enumerate(scored_list, 1):
        sp.rank = i

    return ScoringResponse(
        results=scored_list,
        total_products_evaluated=len(products),
        wizard_input=wizard
    )
