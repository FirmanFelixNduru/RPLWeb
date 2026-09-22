"""
CompareBuy — Comparison Router
Side-by-side product comparison with auto-highlighting.
"""
from fastapi import APIRouter, HTTPException

from app.models import CompareRequest, CompareResponse, SpecHighlight, Product
from app.products import get_product_by_id

router = APIRouter(prefix="/api", tags=["compare"])


# Spec fields to compare, with extraction logic
COMPARE_FIELDS = [
    "display", "processor", "ram", "storage", "battery", "camera",
    "os", "weight", "connectivity", "refresh_rate", "resolution",
    "water_resistance", "gpu", "build_material", "special_features",
    "screen_size", "driver_size", "anc", "codec", "sensors"
]

# Numeric extraction helpers for auto-highlighting
def _extract_numeric(value: str) -> float | None:
    """Try to extract a primary numeric value from a spec string."""
    if not value or value == "N/A":
        return None
    import re
    # Find first number (possibly decimal)
    match = re.search(r'(\d+(?:\.\d+)?)', value.replace(",", ""))
    if match:
        return float(match.group(1))
    return None


def _higher_is_better(field: str) -> bool:
    """For most specs, higher numeric value = better. Exception: weight."""
    return field not in ("weight",)


def _determine_best(field: str, product_values: dict[str, str]) -> str | None:
    """Determine which product has the best value for a spec field."""
    numeric_vals: dict[str, float] = {}
    for pid, val in product_values.items():
        n = _extract_numeric(val)
        if n is not None:
            numeric_vals[pid] = n

    if not numeric_vals:
        return None

    if _higher_is_better(field):
        return max(numeric_vals, key=numeric_vals.get)
    else:
        return min(numeric_vals, key=numeric_vals.get)


@router.post("/compare", response_model=CompareResponse)
def compare_products(req: CompareRequest):
    """
    Compare 2-4 products side by side.
    Returns product data and auto-highlighted best specs.
    """
    products: list[Product] = []
    for pid in req.product_ids:
        product = get_product_by_id(pid)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product '{pid}' not found"
            )
        products.append(product)

    # Build comparison highlights
    highlights: list[SpecHighlight] = []

    for field in COMPARE_FIELDS:
        values: dict[str, str] = {}
        has_value = False
        for p in products:
            val = getattr(p.specs, field, None)
            if val and val != "N/A":
                values[p.id] = val
                has_value = True
            else:
                values[p.id] = "—"

        if has_value:
            best_id = _determine_best(field, values)
            highlights.append(SpecHighlight(
                spec_name=field,
                values=values,
                best_product_id=best_id or ""
            ))

    # Also add score comparisons
    score_fields = [
        ("score_performance", "Skor Performa"),
        ("score_camera", "Skor Kamera"),
        ("score_battery", "Skor Baterai"),
        ("score_display", "Skor Layar"),
        ("score_build_quality", "Skor Build Quality"),
        ("score_value", "Skor Value"),
        ("score_audio", "Skor Audio"),
        ("score_software", "Skor Software"),
    ]

    for attr, label in score_fields:
        values = {}
        for p in products:
            values[p.id] = str(getattr(p, attr, 0))

        best_id = max(values, key=lambda pid: int(values[pid]))
        highlights.append(SpecHighlight(
            spec_name=label,
            values=values,
            best_product_id=best_id
        ))

    # Add price comparison (lower is better)
    price_values = {p.id: str(p.price) for p in products}
    best_price_id = min(price_values, key=lambda pid: int(price_values[pid]))
    highlights.append(SpecHighlight(
        spec_name="Harga (IDR)",
        values=price_values,
        best_product_id=best_price_id
    ))

    # Add warranty comparison
    warranty_values = {p.id: f"{p.warranty.duration_months} bulan (skor: {p.warranty.score})" for p in products}
    best_warranty_id = max(products, key=lambda p: p.warranty.score).id
    highlights.append(SpecHighlight(
        spec_name="Garansi",
        values=warranty_values,
        best_product_id=best_warranty_id
    ))

    return CompareResponse(
        products=products,
        highlights=highlights
    )
