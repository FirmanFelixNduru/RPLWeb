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
import json
import re
import subprocess
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


# ═══════════════════════════════════════════════════════════════════
# Test Suite 5 — Validasi Struktur Garansi Revisi 6
# ═══════════════════════════════════════════════════════════════════
class TestWarrantyRevision6StructuredValidation(unittest.TestCase):

    def setUp(self):
        self.products = get_all_products()
        self.product_map = {p.id: p for p in self.products}

    def test_nullable_structured_fields_accepted(self):
        """Field baru bertipe Optional menerima None tanpa error."""
        w = _warranty(
            parts_warranty_months=None,
            labor_warranty_months=None,
            warranty_type=None,
            battery_warranty_months=None,
            charger_warranty_months=None,
            service_type=None,
            warranty_source_url=None,
            verification_status=None,
        )
        self.assertIsNone(w.parts_warranty_months)
        self.assertIsNone(w.labor_warranty_months)
        self.assertIsNone(w.warranty_type)
        self.assertIsNone(w.battery_warranty_months)
        self.assertIsNone(w.charger_warranty_months)
        self.assertIsNone(w.service_type)
        self.assertIsNone(w.warranty_source_url)
        self.assertIsNone(w.verification_status)

    def test_negative_durations_rejected(self):
        """Durasi garansi spesifik bernilai negatif ditolak."""
        for field in ("parts_warranty_months", "labor_warranty_months", "battery_warranty_months", "charger_warranty_months"):
            with self.assertRaises(ValidationError, msg=f"{field}=-1"):
                _warranty(**{field: -1})

    def test_whitespace_only_strings_rejected(self):
        """Field string baru tidak boleh hanya berisi spasi."""
        for field in ("warranty_type", "service_type", "verification_status", "warranty_source_url"):
            with self.assertRaises(ValidationError, msg=f"{field} whitespace only"):
                _warranty(**{field: "   "})

    def test_no_automatic_fallback_from_duration_months(self):
        """duration_months tidak otomatis mengisi parts atau labor jika tidak disuplai."""
        w = _warranty(duration_months=12)
        self.assertEqual(w.duration_months, 12)
        self.assertIsNone(w.parts_warranty_months)
        self.assertIsNone(w.labor_warranty_months)

    def test_acer_aspire_lp004_special_case(self):
        """lp-004 Acer Aspire 5 membedakan 12 bln suku cadang dan 36 bln servis dengan status SKU belum terverifikasi."""
        p = self.product_map["lp-004"]
        self.assertEqual(p.warranty.duration_months, 12)
        self.assertEqual(p.warranty.parts_warranty_months, 12)
        self.assertEqual(p.warranty.labor_warranty_months, 36)
        self.assertEqual(p.warranty.battery_warranty_months, 12)
        self.assertEqual(p.warranty.charger_warranty_months, 12)
        self.assertEqual(p.warranty.service_type, "Carry-in")
        self.assertEqual(p.warranty.warranty_type, "Resmi Produsen (PT Acer Indonesia)")
        self.assertEqual(
            p.warranty.verification_status,
            "Kebijakan umum produsen terverifikasi, tetapi ketentuan SKU belum terverifikasi"
        )

    def test_asus_rog_lp002_special_case(self):
        """lp-002 ASUS ROG Zephyrus G14 tidak membedakan parts/labor durasi terpisah dan menandai SKU belum terverifikasi."""
        p = self.product_map["lp-002"]
        self.assertEqual(p.warranty.duration_months, 24)
        self.assertIsNone(p.warranty.parts_warranty_months)
        self.assertIsNone(p.warranty.labor_warranty_months)
        self.assertEqual(p.warranty.battery_warranty_months, 12)
        self.assertEqual(p.warranty.charger_warranty_months, 12)
        self.assertEqual(p.warranty.service_type, "Carry-in & On-site")
        self.assertEqual(
            p.warranty.verification_status,
            "Kebijakan umum produsen terverifikasi, tetapi ketentuan SKU belum terverifikasi"
        )
        self.assertEqual(p.warranty.warranty_source_url, "https://www.asus.com/id/content/asus-vip-perfect-warranty/")
        self.assertIn("100% biaya jasa perbaikan dan 100% biaya suku cadang", p.warranty.coverage)
        self.assertIn("ASUS VIP Perfect Warranty", p.warranty.coverage)
        self.assertNotIn("20%", p.warranty.coverage)

    def test_import_market_products_pixel_and_xiaomi14ultra(self):
        """sm-003 Pixel 8 Pro dan sm-004 Xiaomi 14 Ultra ditandai sebagai Pasar Impor / Toko Non-ATPM."""
        for pid in ("sm-003", "sm-004"):
            p = self.product_map[pid]
            self.assertEqual(p.warranty.warranty_type, "Pasar Impor / Toko Non-ATPM")
            self.assertEqual(p.warranty.verification_status, "Garansi distributor atau penjual tertentu")
            self.assertIsNone(p.warranty.parts_warranty_months)
            self.assertIsNone(p.warranty.labor_warranty_months)
            self.assertIsNone(p.warranty.battery_warranty_months)
            self.assertIsNone(p.warranty.charger_warranty_months)

    def test_poco_x6pro_sm005_battery_is_none_charger_is_6(self):
        """sm-005 POCO X6 Pro baterai None (belum terverifikasi terpisah), charger 6 bulan."""
        p = self.product_map["sm-005"]
        self.assertEqual(p.warranty.duration_months, 15)
        self.assertIsNone(p.warranty.parts_warranty_months)
        self.assertIsNone(p.warranty.labor_warranty_months)
        self.assertIsNone(p.warranty.battery_warranty_months)
        self.assertEqual(p.warranty.charger_warranty_months, 6)
        self.assertEqual(p.warranty.verification_status, "Ketentuan spesifik SKU terverifikasi")

    def test_all_20_products_have_valid_warranty_type_and_verification_status(self):
        """Seluruh 20 produk memiliki warranty_type dan verification_status yang terdaftar."""
        valid_types = {
            "Resmi Produsen (SEIN)",
            "Resmi Produsen (PT Acer Indonesia)",
            "Resmi Produsen (PT ASUS Technology Indonesia)",
            "Resmi Produsen (PT Lenovo Indonesia)",
            "Resmi Produsen (PT Xiaomi Technology Indonesia)",
            "Resmi Produsen (PT Sony Indonesia)",
            "Resmi Distributor / Authorized Reseller",
            "Pasar Impor / Toko Non-ATPM",
            "Garansi distributor atau penjual tertentu"
        }
        valid_statuses = {
            "Ketentuan spesifik SKU terverifikasi",
            "Kebijakan umum produsen terverifikasi, tetapi ketentuan SKU belum terverifikasi",
            "Garansi distributor atau penjual tertentu",
            "Belum terverifikasi"
        }
        for p in self.products:
            self.assertIn(p.warranty.warranty_type, valid_types, msg=f"{p.id} warranty_type")
            self.assertIn(p.warranty.verification_status, valid_statuses, msg=f"{p.id} verification_status")
            self.assertTrue(p.warranty.warranty_source_url and p.warranty.warranty_source_url.startswith("http"), msg=p.id)

    def test_api_products_serializes_structured_fields(self):
        """GET /api/products dan GET /api/products/lp-004 mengembalikan field-field terstruktur baru."""
        res = client.get("/api/products/lp-004")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        w = data["warranty"]
        self.assertEqual(w["duration_months"], 12)
        self.assertEqual(w["parts_warranty_months"], 12)
        self.assertEqual(w["labor_warranty_months"], 36)
        self.assertEqual(w["warranty_type"], "Resmi Produsen (PT Acer Indonesia)")
        self.assertEqual(w["service_type"], "Carry-in")
        self.assertEqual(w["verification_status"], "Kebijakan umum produsen terverifikasi, tetapi ketentuan SKU belum terverifikasi")

    def test_frontend_data_matches_backend_warranty(self):
        """Memverifikasi frontend/src/data/products.js konsisten dengan backend/app/products.py."""
        frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "data", "products.js")
        if not os.path.exists(frontend_path):
            self.skipTest("Frontend path not found from current directory")
        with open(frontend_path, "r", encoding="utf-8") as f:
            fe_text = f.read()
        for p in self.products:
            self.assertTrue(f"id: '{p.id}'" in fe_text or f'id: "{p.id}"' in fe_text, msg=p.id)
            self.assertIn(f"duration_months: {p.warranty.duration_months}", fe_text)

    def test_product_card_badge_label_evaluation(self):
        """Memverifikasi bahwa fungsi JavaScript getWarrantyBadgeLabel di ProductCard.js
        mengevaluasi badge secara konservatif langsung melalui runtime Node.js."""
        frontend_card_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "frontend", "src", "components", "catalog", "ProductCard.js"
        )
        if not os.path.exists(frontend_card_path):
            self.skipTest("ProductCard.js not found from current directory")

        with open(frontend_card_path, "r", encoding="utf-8") as f:
            code = f.read()

        match = re.search(r"export function getWarrantyBadgeLabel\s*\([\s\S]*?\n\}", code)
        self.assertIsNotNone(match, "getWarrantyBadgeLabel function must be exported from ProductCard.js")
        fn_code = match.group(0).replace("export function", "function")

        def evaluate_in_node(warranty_dict):
            js_script = f"""
            const vm = require('vm');
            {fn_code}
            const input = JSON.parse(process.argv[1]);
            const res = getWarrantyBadgeLabel(input);
            process.stdout.write(res === undefined ? 'undefined' : String(res));
            """
            proc = subprocess.run(
                ["node", "-e", js_script, json.dumps(warranty_dict)],
                capture_output=True,
                text=True,
                check=True
            )
            return proc.stdout

        # 1. Status SKU belum terverifikasi: ASUS ROG Zephyrus G14 (lp-002) -> "Acuan 24 Bln"
        asus = self.product_map["lp-002"].warranty.model_dump()
        self.assertEqual(evaluate_in_node(asus), "Acuan 24 Bln")

        # 2. Status SKU belum terverifikasi: Acer Aspire 5 (lp-004) -> "Acuan 12 Bln"
        acer = self.product_map["lp-004"].warranty.model_dump()
        self.assertEqual(evaluate_in_node(acer), "Acuan 12 Bln")

        # 3. Produk impor: Google Pixel 8 Pro (sm-003) -> "Acuan 12 Bln"
        pixel = self.product_map["sm-003"].warranty.model_dump()
        self.assertEqual(evaluate_in_node(pixel), "Acuan 12 Bln")

        # 4. Produk impor: Xiaomi 14 Ultra (sm-004) -> "Acuan 12 Bln"
        xiaomi = self.product_map["sm-004"].warranty.model_dump()
        self.assertEqual(evaluate_in_node(xiaomi), "Acuan 12 Bln")

        # 5. Garansi distributor/penjual tertentu: QCY MeloBuds ANC (tw-004) -> "Acuan 6 Bln"
        qcy = self.product_map["tw-004"].warranty.model_dump()
        self.assertEqual(evaluate_in_node(qcy), "Acuan 6 Bln")

        # 6. Status SKU terverifikasi resmi:
        sein = self.product_map["sm-001"].warranty.model_dump()
        self.assertEqual(evaluate_in_node(sein), "Garansi 12 Bln")

        apple = self.product_map["sm-002"].warranty.model_dump()
        self.assertEqual(evaluate_in_node(apple), "Garansi 12 Bln")

        poco = self.product_map["sm-005"].warranty.model_dump()
        self.assertEqual(evaluate_in_node(poco), "Garansi 15 Bln")

        lenovo = self.product_map["lp-003"].warranty.model_dump()
        self.assertEqual(evaluate_in_node(lenovo), "Garansi 36 Bln")

        # 7. Status null atau kosong (harus konservatif acuan, bukan klaim resmi)
        null_status = {"duration_months": 12, "warranty_type": "Resmi Produsen (SEIN)", "verification_status": None}
        self.assertEqual(evaluate_in_node(null_status), "Acuan 12 Bln")

        empty_status = {"duration_months": 12, "warranty_type": "Resmi Produsen (SEIN)", "verification_status": ""}
        self.assertEqual(evaluate_in_node(empty_status), "Acuan 12 Bln")

        # 8. Status baru yang tidak dikenal (harus konservatif acuan)
        unknown_status = {"duration_months": 24, "warranty_type": "Resmi Produsen", "verification_status": "Status Baru Belum Terdaftar"}
        self.assertEqual(evaluate_in_node(unknown_status), "Acuan 24 Bln")

        # 9. duration_months bernilai null / tidak tersedia (tidak boleh ada angka fallback)
        null_duration = {"duration_months": None, "warranty_type": "Resmi Produsen (SEIN)", "verification_status": "Ketentuan spesifik SKU terverifikasi"}
        self.assertEqual(evaluate_in_node(null_duration), "Belum Terverifikasi")

        zero_duration = {"duration_months": 0, "warranty_type": "Resmi Produsen (SEIN)", "verification_status": "Ketentuan spesifik SKU terverifikasi"}
        self.assertEqual(evaluate_in_node(zero_duration), "Belum Terverifikasi")

        # 10. warranty bernilai null
        self.assertEqual(evaluate_in_node(None), "Belum Terverifikasi")


if __name__ == "__main__":
    unittest.main(verbosity=2)
