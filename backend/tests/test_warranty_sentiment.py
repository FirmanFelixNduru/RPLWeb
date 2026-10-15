"""
CompareBuy — Unit Tests: After-Sales Warranty Index & Review Sentiment Validation
Fitur 5 – MVP Version 1

Menguji boundary model WarrantyInfo & ReviewSentiment di backend/app/models.py,
integritas data kurasi 20 produk katalog aktual, dan penentuan
best_warranty_id pada endpoint POST /api/compare.
Menggunakan standar library unittest Python.
"""
import sys
import os
import unittest

# Pastikan modul app dapat diimpor dari direktori backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests import _pretty  # noqa: F401  (format output [OK] ...)

from pydantic import ValidationError
from fastapi.testclient import TestClient
from app.main import app
from app.models import WarrantyInfo, ReviewSentiment
from app.products import get_all_products

client = TestClient(app)


def _warranty(**overrides) -> WarrantyInfo:
    data = dict(
        duration_months=12,
        coverage="Garansi resmi - hardware",
        claim_ease=7,
        official_service_centers=10,
        score=80.0,
    )
    data.update(overrides)
    return WarrantyInfo(**data)


def _sentiment(**overrides) -> ReviewSentiment:
    data = dict(
        overall_score=4.5,
        total_reviews=100,
        pros=["Layar bagus"],
        cons=["Harga mahal"],
        summary="Ulasan positif",
    )
    data.update(overrides)
    return ReviewSentiment(**data)


# ═══════════════════════════════════════════════════════════════════
# Test Suite 1 — Boundary WarrantyInfo
# ═══════════════════════════════════════════════════════════════════
class TestWarrantyInfoBoundaries(unittest.TestCase):

    def test_valid_warranty_is_accepted(self):
        """Data garansi valid diterima."""
        self.assertEqual(_warranty().duration_months, 12)

    def test_zero_duration_is_accepted(self):
        """Durasi garansi 0 bulan diterima."""
        self.assertEqual(_warranty(duration_months=0).duration_months, 0)

    def test_negative_duration_rejected(self):
        """Durasi garansi negatif ditolak."""
        with self.assertRaises(ValidationError):
            _warranty(duration_months=-1)

    def test_claim_ease_boundaries_1_and_10_accepted(self):
        """claim_ease batas 1 dan 10 diterima."""
        self.assertEqual(_warranty(claim_ease=1).claim_ease, 1)
        self.assertEqual(_warranty(claim_ease=10).claim_ease, 10)

    def test_claim_ease_out_of_range_rejected(self):
        """claim_ease di luar 1-10 ditolak."""
        for bad in (0, 11):
            with self.assertRaises(ValidationError, msg=f"claim_ease={bad}"):
                _warranty(claim_ease=bad)

    def test_score_boundaries_0_and_100_accepted(self):
        """Skor garansi batas 0 dan 100 diterima."""
        self.assertEqual(_warranty(score=0.0).score, 0.0)
        self.assertEqual(_warranty(score=100.0).score, 100.0)

    def test_score_out_of_range_rejected(self):
        """Skor garansi di luar 0-100 ditolak."""
        for bad in (-0.1, 100.1):
            with self.assertRaises(ValidationError, msg=f"score={bad}"):
                _warranty(score=bad)

    def test_negative_service_centers_rejected(self):
        """Jumlah service center negatif ditolak."""
        with self.assertRaises(ValidationError):
            _warranty(official_service_centers=-1)

    def test_empty_coverage_rejected(self):
        """Coverage string kosong ditolak."""
        with self.assertRaises(ValidationError):
            _warranty(coverage="")

    def test_whitespace_only_coverage_rejected(self):
        """Coverage hanya spasi ditolak."""
        with self.assertRaises(ValidationError):
            _warranty(coverage="   ")

    def test_short_non_blank_coverage_is_accepted(self):
        """Tidak ada batas panjang minimum arbitrer selain non-blank."""
        self.assertEqual(_warranty(coverage="ab").coverage, "ab")


# ═══════════════════════════════════════════════════════════════════
# Test Suite 2 — Boundary ReviewSentiment
# ═══════════════════════════════════════════════════════════════════
class TestReviewSentimentBoundaries(unittest.TestCase):

    def test_valid_sentiment_is_accepted(self):
        """Data sentimen valid diterima."""
        self.assertEqual(_sentiment().overall_score, 4.5)

    def test_overall_score_boundaries_0_and_5_accepted(self):
        """overall_score batas 0 dan 5 diterima."""
        self.assertEqual(_sentiment(overall_score=0.0).overall_score, 0.0)
        self.assertEqual(_sentiment(overall_score=5.0).overall_score, 5.0)

    def test_overall_score_out_of_range_rejected(self):
        """overall_score di luar 0-5 ditolak."""
        for bad in (-0.1, 5.1):
            with self.assertRaises(ValidationError, msg=f"overall_score={bad}"):
                _sentiment(overall_score=bad)

    def test_negative_total_reviews_rejected(self):
        """total_reviews negatif ditolak."""
        with self.assertRaises(ValidationError):
            _sentiment(total_reviews=-1)

    def test_empty_pros_item_rejected(self):
        """Elemen pros kosong ditolak."""
        with self.assertRaises(ValidationError):
            _sentiment(pros=["Bagus", ""])

    def test_whitespace_cons_item_rejected(self):
        """Elemen cons hanya spasi ditolak."""
        with self.assertRaises(ValidationError):
            _sentiment(cons=["   "])

    def test_blank_items_are_rejected_not_silently_dropped(self):
        """Elemen kosong wajib melempar ValidationError, bukan dibuang diam-diam."""
        with self.assertRaises(ValidationError):
            _sentiment(pros=["", "Bagus"], cons=["Mahal", "  "])

    def test_empty_lists_are_accepted(self):
        """List pros/cons kosong diterima."""
        s = _sentiment(pros=[], cons=[])
        self.assertEqual(s.pros, [])
        self.assertEqual(s.cons, [])


# ═══════════════════════════════════════════════════════════════════
# Test Suite 3 — Integritas Data Kurasi 20 Produk Aktual
# ═══════════════════════════════════════════════════════════════════
class TestCuratedCatalogIntegrity(unittest.TestCase):

    def setUp(self):
        self.products = get_all_products()

    def test_catalog_has_exactly_20_products(self):
        """Katalog memuat tepat 20 produk aktual."""
        self.assertEqual(len(self.products), 20)

    def test_tws_ids_use_tw_prefix(self):
        """ID kategori TWS memakai prefix tw-."""
        tws_ids = sorted(p.id for p in self.products if p.category.value == "tws")
        self.assertEqual(tws_ids, ["tw-001", "tw-002", "tw-003", "tw-004"])

    def test_all_warranty_scores_within_0_100(self):
        """Seluruh skor garansi kurasi berada dalam 0-100."""
        for p in self.products:
            self.assertTrue(0.0 <= p.warranty.score <= 100.0, msg=p.id)

    def test_all_warranty_data_revalidates_cleanly(self):
        """Re-validasi seluruh data garansi kurasi lewat model terkini."""
        for p in self.products:
            WarrantyInfo(**p.warranty.model_dump())
            self.assertTrue(p.warranty.coverage.strip(), msg=p.id)

    def test_all_review_sentiment_revalidates_cleanly(self):
        """Re-validasi seluruh data sentimen kurasi: tidak ada pros/cons kosong."""
        for p in self.products:
            ReviewSentiment(**p.review_sentiment.model_dump())
            for item in p.review_sentiment.pros + p.review_sentiment.cons:
                self.assertTrue(item.strip(), msg=p.id)


# ═══════════════════════════════════════════════════════════════════
# Test Suite 4 — Penentuan best_warranty_id pada /api/compare
# ═══════════════════════════════════════════════════════════════════
class TestBestWarrantySelection(unittest.TestCase):

    def _garansi_highlight(self, ids):
        res = client.post("/api/compare", json={"product_ids": ids})
        self.assertEqual(res.status_code, 200, msg=res.text)
        data = res.json()
        highlight = next(h for h in data["highlights"] if h["spec_name"] == "Garansi")
        return data, highlight

    def test_best_warranty_is_product_with_highest_score(self):
        """best_warranty_id adalah produk dengan skor garansi tertinggi."""
        ids = ["sm-001", "sm-002", "sm-003"]
        data, highlight = self._garansi_highlight(ids)
        expected = max(data["products"], key=lambda p: p["warranty"]["score"])["id"]
        self.assertEqual(highlight["best_product_id"], expected)

    def test_best_warranty_matches_catalog_curated_scores(self):
        """best_warranty_id konsisten dengan skor kurasi katalog."""
        by_id = {p.id: p for p in get_all_products()}
        ids = ["lp-003", "lp-004", "tw-004"]
        _, highlight = self._garansi_highlight(ids)
        expected = max((by_id[i] for i in ids), key=lambda p: p.warranty.score).id
        self.assertEqual(highlight["best_product_id"], expected)

    def test_warranty_highlight_covers_all_compared_products(self):
        """Highlight garansi mencakup semua produk yang dibandingkan."""
        ids = ["sw-001", "sw-002"]
        _, highlight = self._garansi_highlight(ids)
        self.assertEqual(set(highlight["values"].keys()), set(ids))


if __name__ == "__main__":
    unittest.main(verbosity=2)
