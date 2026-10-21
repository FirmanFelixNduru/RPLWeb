"""
CompareBuy — Comparison Router
Side-by-side product comparison with auto-highlighting.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from sqlalchemy.orm import Session

from app.models import (
    CompareRequest, CompareResponse, SpecHighlight, Product,
    SectorWinSummary
)
from app.products import get_product_by_id as get_fallback_product
from app.db import get_db
from app.repositories import catalog_repo

router = APIRouter(prefix="/api", tags=["compare"])


# Spec fields to compare
COMPARE_FIELDS = [
    "display", "processor", "ram", "storage", "battery", "camera",
    "os", "weight", "connectivity", "refresh_rate", "resolution",
    "water_resistance", "gpu", "build_material", "special_features",
    "screen_size", "driver_size", "anc", "codec", "sensors",
    "ports", "charging"
]

# Descriptive fields that must NOT extract arbitrary numbers from text strings
DESCRIPTIVE_FIELDS = {
    "processor", "os", "ports", "connectivity", "sensors",
    "build_material", "special_features"
}

# 8 dimensions and their category relevance
DIMENSION_FIELDS = [
    ("score_performance", "Skor Performa", "performance"),
    ("score_camera", "Skor Kamera", "camera"),
    ("score_battery", "Skor Baterai", "battery"),
    ("score_display", "Skor Layar", "display"),
    ("score_build_quality", "Skor Build Quality", "build_quality"),
    ("score_value", "Skor Value", "value"),
    ("score_audio", "Skor Audio", "audio"),
    ("score_software", "Skor Software", "software"),
]

CATEGORY_RELEVANT_DIMENSIONS = {
    "smartphone": ["performance", "camera", "battery", "display", "build_quality", "value", "audio", "software"],
    "laptop": ["performance", "camera", "battery", "display", "build_quality", "value", "audio", "software"],
    "tablet": ["performance", "camera", "battery", "display", "build_quality", "value", "audio", "software"],
    "smartwatch": ["performance", "battery", "display", "build_quality", "value", "audio", "software"],
    "tws": ["performance", "battery", "build_quality", "value", "audio", "software"],
}


def _extract_numeric(value: str, field: str = "") -> float | None:
    """Try to extract a primary numeric value from a spec string.
    Normalizes:
    - storage: TB -> GB (x 1024)
    - weight: kg -> g (x 1000)
    - currency: Rp / IDR
    Does not extract arbitrary numbers from descriptive fields.
    """
    if not value or value in ("N/A", "—", "-"):
        return None
    if field in DESCRIPTIVE_FIELDS:
        return None

    import re
    # Currency amount (Rp / IDR) — isolate the number after the currency token
    currency_match = re.search(r'\b(?:rp|idr)\b\.?\s*([\d\.,]+)', value, re.IGNORECASE)
    if currency_match:
        digits = re.sub(r'[\.,]', '', currency_match.group(1))
        if digits:
            return float(digits)

    # Storage normalization: TB -> GB
    if field == "storage" or re.search(r'\b\d+(?:\.\d+)?\s*(?:tb|gb)\b', value, re.IGNORECASE):
        tb_match = re.search(r'\b(\d+(?:\.\d+)?)\s*tb\b', value, re.IGNORECASE)
        if tb_match:
            return float(tb_match.group(1)) * 1024.0
        gb_match = re.search(r'\b(\d+(?:\.\d+)?)\s*gb\b', value, re.IGNORECASE)
        if gb_match:
            return float(gb_match.group(1))

    # Weight normalization: kg -> g
    if field == "weight" or re.search(r'\b\d+(?:\.\d+)?\s*(?:kg|g)\b', value, re.IGNORECASE):
        kg_match = re.search(r'\b(\d+(?:\.\d+)?)\s*kg\b', value, re.IGNORECASE)
        if kg_match:
            return float(kg_match.group(1)) * 1000.0
        g_match = re.search(r'\b(\d+(?:\.\d+)?)\s*g\b', value, re.IGNORECASE)
        if g_match:
            return float(g_match.group(1))

    # Dot-separated thousands (e.g. 19.999.000) — only the matched text is used
    thousands_match = re.search(r'\b\d{1,3}(?:\.\d{3})+\b', value)
    if thousands_match:
        return float(thousands_match.group(0).replace(".", ""))

    # Find first number (possibly decimal)
    match = re.search(r'(\d+(?:\.\d+)?)', value.replace(",", ""))
    if match:
        return float(match.group(1))
    return None


def _higher_is_better(field: str) -> bool:
    """For most specs, higher numeric value = better.
    Exceptions (lower is better): weight, price.
    """
    return field not in ("weight", "price")


def _determine_best_with_ties(field: str, product_values: dict[str, str]) -> tuple[str | None, list[str], bool]:
    """Determine best product(s), detecting ties and unit incompatibilities."""
    if field in DESCRIPTIVE_FIELDS:
        return None, [], False

    # Battery comparability check: mAh vs Wh
    if field == "battery":
        has_mah = any("mah" in (val or "").lower() for val in product_values.values() if val and val != "—")
        has_wh = any("wh" in (val or "").lower() for val in product_values.values() if val and val != "—")
        if has_mah and has_wh:
            # Incompatible battery units (e.g. laptop vs smartphone)
            return None, [], False

    numeric_vals: dict[str, float] = {}
    for pid, val in product_values.items():
        if not val or val in ("—", "N/A", "Tidak Ada"):
            continue
        n = _extract_numeric(val, field)
        if n is not None:
            numeric_vals[pid] = n

    if not numeric_vals:
        return None, [], False

    if _higher_is_better(field):
        target_val = max(numeric_vals.values())
    else:
        target_val = min(numeric_vals.values())

    winners = [pid for pid, val in numeric_vals.items() if val == target_val]
    is_tie = len(winners) > 1
    best_id = "" if is_tie else (winners[0] if winners else None)
    return best_id, winners, is_tie


def _determine_best(field: str, product_values: dict[str, str]) -> str | None:
    """Backward-compatible helper returning single best_product_id or None."""
    _, winners, _ = _determine_best_with_ties(field, product_values)
    return winners[0] if winners else None


@router.post("/compare", response_model=CompareResponse)
def compare_products(req: CompareRequest, db: Optional[Session] = Depends(get_db)):
    """
    Compare 2-4 products side by side.
    Returns product data, auto-highlighted best specs with tie support,
    and structured 8-dimension win-count evaluation.
    """

    products: list[Product] = []
    for pid in req.product_ids:
        product = None
        if db is not None:
            try:
                product = catalog_repo.get_product_by_id(db, pid)
            except Exception:
                pass
        if not product:
            product = get_fallback_product(pid)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product '{pid}' not found"
            )
        products.append(product)

    # Determine category consistency
    categories = set(p.category.value if hasattr(p.category, "value") else str(p.category) for p in products)
    is_same_category = len(categories) == 1
    current_category = next(iter(categories)) if is_same_category else None
    p_map = {p.id: p for p in products}

    # Build comparison highlights for specs
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
            best_id, best_ids, is_tie = _determine_best_with_ties(field, values)
            highlights.append(SpecHighlight(
                spec_name=field,
                values=values,
                best_product_id=best_id or "",
                best_product_ids=best_ids,
                is_tie=is_tie
            ))

    # Win-count tracking for 8 dimensions
    win_counts: dict[str, int] = {p.id: 0 for p in products}
    winning_sectors: dict[str, list[str]] = {p.id: [] for p in products}
    tied_sectors: dict[str, list[str]] = {p.id: [] for p in products}
    tied_sectors_summary: list[str] = []

    applicable_dimensions = CATEGORY_RELEVANT_DIMENSIONS.get(current_category, []) if is_same_category else []

    # Add 8 dimension score comparisons
    for attr, label, dim_key in DIMENSION_FIELDS:
        values: dict[str, str] = {}
        is_applicable = is_same_category and (dim_key in applicable_dimensions)

        if is_same_category and not is_applicable:
            # Dimension not applicable for this category (e.g. camera on TWS/Smartwatch)
            values = {p.id: "— (Tidak Berlaku)" for p in products}
            highlights.append(SpecHighlight(
                spec_name=label,
                values=values,
                best_product_id="",
                best_product_ids=[],
                is_tie=False
            ))
            continue

        for p in products:
            val = getattr(p, attr, None)
            if val is not None:
                values[p.id] = str(val)
            else:
                values[p.id] = "—"

        has_missing = any(values[p.id] == "—" for p in products)

        if is_same_category and not has_missing and values:
            numeric_scores = {pid: int(v) for pid, v in values.items()}
            max_val = max(numeric_scores.values())
            winners = [pid for pid, score in numeric_scores.items() if score == max_val]

            if len(winners) > 1:
                is_tie = True
                best_id = ""  # Poin 1: Kosongkan saat seri agar klien lama tidak membuat klaim pemenang tunggal
                best_ids = winners
                for w_id in winners:
                    win_counts[w_id] += 1
                    tied_sectors[w_id].append(f"{label} (Seri)")
                winner_names = [p_map[w].name for w in winners]
                tied_sectors_summary.append(f"{label}: Seri antara {', '.join(winner_names)} ({max_val})")
            else:
                is_tie = False
                best_id = winners[0]
                best_ids = winners
                win_counts[best_id] += 1
                winning_sectors[best_id].append(label)

            highlights.append(SpecHighlight(
                spec_name=label,
                values=values,
                best_product_id=best_id,
                best_product_ids=best_ids,
                is_tie=is_tie
            ))
        else:
            highlights.append(SpecHighlight(
                spec_name=label,
                values=values,
                best_product_id="",
                best_product_ids=[],
                is_tie=False
            ))

    # Add price comparison (lower is better)
    price_values = {p.id: str(p.price) for p in products}
    numeric_prices = {pid: int(val) for pid, val in price_values.items()}
    min_price = min(numeric_prices.values())
    cheapest_ids = [pid for pid, val in numeric_prices.items() if val == min_price]
    is_price_tie = len(cheapest_ids) > 1

    # Revisi 5 & Poin 1:
    # 1. Pada komparasi lintas kategori, jangan menetapkan pemenang harga universal
    # 2. Pada hasil seri, kosongkan best_product_id agar klien lama tidak mengklaim pemenang tunggal
    if not is_same_category:
        price_best_id = ""
        price_best_ids = []
        is_price_tie = False
    elif is_price_tie:
        price_best_id = ""
        price_best_ids = cheapest_ids
    else:
        price_best_id = cheapest_ids[0]
        price_best_ids = cheapest_ids

    highlights.append(SpecHighlight(
        spec_name="Harga (IDR)",
        values=price_values,
        best_product_id=price_best_id,
        best_product_ids=price_best_ids,
        is_tie=is_price_tie
    ))

    # Add warranty comparison
    warranty_values = {p.id: f"{p.warranty.duration_months} bulan (skor: {p.warranty.score})" for p in products}
    max_w_score = max(p.warranty.score for p in products)
    top_w_products = [p.id for p in products if p.warranty.score == max_w_score]
    is_w_tie = len(top_w_products) > 1
    best_warranty_id = "" if is_w_tie else top_w_products[0]

    highlights.append(SpecHighlight(
        spec_name="Garansi",
        values=warranty_values,
        best_product_id=best_warranty_id,
        best_product_ids=top_w_products,
        is_tie=is_w_tie
    ))

    # Build Win-Count Summary
    win_summary: list[SectorWinSummary] = []
    if is_same_category:
        for p in products:
            win_summary.append(SectorWinSummary(
                product_id=p.id,
                product_name=p.name,
                win_count=win_counts[p.id],
                winning_sectors=winning_sectors[p.id],
                tied_sectors=tied_sectors[p.id],
                solo_wins=len(winning_sectors[p.id]),
                shared_wins=len(tied_sectors[p.id])
            ))

    return CompareResponse(
        products=products,
        highlights=highlights,
        is_same_category=is_same_category,
        category=current_category,
        win_summary=win_summary,
        tied_sectors_summary=tied_sectors_summary
    )
