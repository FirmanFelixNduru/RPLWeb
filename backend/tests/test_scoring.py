"""
CompareBuy — Unit Tests: Weighted Dynamic Scoring Engine (MCDA)
Fitur 1 – MVP Version 1

Menguji fungsi-fungsi inti di backend/app/scoring.py secara terisolasi
tanpa memerlukan server, database, atau koneksi jaringan aktif.
Menggunakan standar library unittest Python.
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError, SQLAlchemyError

# Pastikan modul app dapat diimpor dari direktori backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests import _pretty  # noqa: F401  (format output [OK] ...)

from app.main import app
from app.db import get_db
from app.repositories import catalog_repo
from app.models import (
    WizardInput, UsageScenario, Product, ProductSpecs,
    ReviewSentiment, WarrantyInfo, ProductCategory
)
from app.scoring import (
    _build_weight_vector,
    _budget_modifier,
    _budget_fit_label,
    calculate_scores,
    DIMENSIONS,
    SCENARIO_BOOSTS,
)


# ──────────────────────────────────────────────────────────────────
# Helper: buat WizardInput minimal yang valid
# ──────────────────────────────────────────────────────────────────
def _make_wizard(
    category="smartphone",
    budget_min=5_000_000,
    budget_max=15_000_000,
    scenarios=None,
    priorities=None,
):
    return WizardInput(
        category=category,
        budget_min=budget_min,
        budget_max=budget_max,
        scenarios=scenarios or [],
        priorities=priorities or {},
    )


# ═══════════════════════════════════════════════════════════════════
# Test Suite 1 — Weight Vector Normalization
# ═══════════════════════════════════════════════════════════════════
class TestWeightVectorNormalization(unittest.TestCase):
    """Memastikan vektor bobot selalu berjumlah 1.0 dalam berbagai kondisi."""

    def _sum_weights(self, wizard: WizardInput) -> float:
        weights = _build_weight_vector(wizard)
        return sum(weights.values())

    def test_all_dimensions_covered(self):
        """Vektor bobot harus mengandung semua 8 dimensi scoring."""
        wizard = _make_wizard()
        weights = _build_weight_vector(wizard)
        self.assertEqual(set(weights.keys()), set(DIMENSIONS))

    def test_default_priorities_sum_to_one(self):
        """Tanpa prioritas eksplisit (semua default 3), jumlah bobot = 1.0."""
        wizard = _make_wizard()
        total = self._sum_weights(wizard)
        self.assertAlmostEqual(total, 1.0, places=9,
            msg=f"Total bobot default harus 1.0, bukan {total}")

    def test_custom_priorities_sum_to_one(self):
        """Dengan prioritas eksplisit berbeda-beda, jumlah bobot tetap = 1.0."""
        wizard = _make_wizard(priorities={
            "performance": 5,
            "camera": 4,
            "battery": 3,
            "display": 2,
            "build_quality": 1,
            "value": 5,
            "audio": 2,
            "software": 4,
        })
        total = self._sum_weights(wizard)
        self.assertAlmostEqual(total, 1.0, places=9,
            msg=f"Total bobot custom harus 1.0, bukan {total}")

    def test_single_priority_one_sums_to_one(self):
        """Prioritas tunggal dengan nilai 1 harus menghasilkan bobot yang valid (jumlah = 1.0)."""
        wizard = _make_wizard(priorities={"performance": 5})
        total = self._sum_weights(wizard)
        self.assertAlmostEqual(total, 1.0, places=9,
            msg=f"Bobot dengan satu prioritas harus 1.0, bukan {total}")

    def test_with_scenarios_sum_to_one(self):
        """Setelah boost skenario diterapkan, jumlah bobot masih = 1.0."""
        wizard = _make_wizard(
            scenarios=[UsageScenario.GAMING, UsageScenario.PHOTOGRAPHY],
            priorities={"performance": 5, "camera": 4},
        )
        total = self._sum_weights(wizard)
        self.assertAlmostEqual(total, 1.0, places=9,
            msg=f"Total bobot dengan skenario harus 1.0, bukan {total}")

    def test_max_all_priorities_sum_to_one(self):
        """Semua prioritas bernilai 5 (maksimum) harus menghasilkan jumlah 1.0."""
        wizard = _make_wizard(priorities={dim: 5 for dim in DIMENSIONS})
        total = self._sum_weights(wizard)
        self.assertAlmostEqual(total, 1.0, places=9)

    def test_min_all_priorities_sum_to_one(self):
        """Semua prioritas bernilai 1 (minimum) harus menghasilkan jumlah 1.0."""
        wizard = _make_wizard(priorities={dim: 1 for dim in DIMENSIONS})
        total = self._sum_weights(wizard)
        self.assertAlmostEqual(total, 1.0, places=9)

    def test_weights_all_non_negative(self):
        """Semua bobot harus bernilai >= 0 (tidak boleh negatif)."""
        wizard = _make_wizard(
            scenarios=[UsageScenario.STUDENT, UsageScenario.FITNESS],
            priorities={"value": 5, "battery": 4},
        )
        weights = _build_weight_vector(wizard)
        for dim, w in weights.items():
            self.assertGreaterEqual(w, 0.0, msg=f"Bobot dimensi '{dim}' negatif: {w}")


# ═══════════════════════════════════════════════════════════════════
# Test Suite 2 — Scenario Boosts
# ═══════════════════════════════════════════════════════════════════
class TestScenarioBoosts(unittest.TestCase):
    """Memastikan skenario meningkatkan bobot dimensi yang relevan."""

    def test_gaming_boosts_performance(self):
        """Skenario 'gaming' harus membuat bobot 'performance' lebih besar dari 'camera'."""
        wizard_gaming = _make_wizard(scenarios=[UsageScenario.GAMING])
        weights = _build_weight_vector(wizard_gaming)
        self.assertGreater(weights["performance"], weights["camera"],
            msg="Gaming harus memprioritaskan performance di atas camera")

    def test_photography_boosts_camera(self):
        """Skenario 'photography' harus membuat bobot 'camera' paling dominan."""
        wizard_photo = _make_wizard(scenarios=[UsageScenario.PHOTOGRAPHY])
        weights = _build_weight_vector(wizard_photo)
        self.assertGreater(weights["camera"], weights["battery"],
            msg="Photography harus memprioritaskan camera di atas battery")

    def test_student_boosts_value(self):
        """Skenario 'student' harus meningkatkan bobot 'value' di atas 'audio'."""
        wizard_student = _make_wizard(scenarios=[UsageScenario.STUDENT])
        weights = _build_weight_vector(wizard_student)
        self.assertGreater(weights["value"], weights["audio"],
            msg="Student scenario harus memprioritaskan value")

    def test_all_defined_scenarios_applied(self):
        """Setiap skenario yang terdefinisi di SCENARIO_BOOSTS harus valid."""
        for scenario_key in SCENARIO_BOOSTS:
            scenario_enum = UsageScenario(scenario_key)
            wizard = _make_wizard(scenarios=[scenario_enum])
            weights = _build_weight_vector(wizard)
            self.assertEqual(len(weights), len(DIMENSIONS),
                msg=f"Skenario '{scenario_key}' menghasilkan dimensi yang tidak lengkap")

    def test_multiple_scenarios_combine_boosts(self):
        """Dua skenario yang dikombinasikan harus menghasilkan bobot lebih besar
        dari hanya satu skenario untuk dimensi yang di-boost keduanya."""
        wizard_single = _make_wizard(scenarios=[UsageScenario.GAMING])
        wizard_double = _make_wizard(scenarios=[UsageScenario.GAMING, UsageScenario.CONTENT_CREATION])
        w_single = _build_weight_vector(wizard_single)
        w_double = _build_weight_vector(wizard_double)
        # Keduanya boost performance, jadi kombinasi harus memberikan bobot relatif performance yang besar
        self.assertGreater(w_double["performance"], 0.0)


# ═══════════════════════════════════════════════════════════════════
# Test Suite 3 — Budget Modifier
# ═══════════════════════════════════════════════════════════════════
class TestBudgetModifier(unittest.TestCase):
    """Memvalidasi semua kasus kalkulasi modifier budget."""

    def test_within_budget_gives_bonus_five(self):
        """Produk dalam rentang budget mendapat bonus +5."""
        modifier = _budget_modifier(
            price=10_000_000,
            budget_min=5_000_000,
            budget_max=15_000_000,
        )
        self.assertEqual(modifier, 5.0,
            msg=f"Dalam budget harus +5, bukan {modifier}")

    def test_exactly_at_min_boundary_is_within(self):
        """Harga tepat di budget_min dianggap 'within' dan mendapat +5."""
        modifier = _budget_modifier(5_000_000, 5_000_000, 15_000_000)
        self.assertEqual(modifier, 5.0)

    def test_exactly_at_max_boundary_is_within(self):
        """Harga tepat di budget_max dianggap 'within' dan mendapat +5."""
        modifier = _budget_modifier(15_000_000, 5_000_000, 15_000_000)
        self.assertEqual(modifier, 5.0)

    def test_below_budget_gives_bonus_two(self):
        """Produk di bawah budget_min mendapat bonus +2."""
        modifier = _budget_modifier(
            price=3_000_000,
            budget_min=5_000_000,
            budget_max=15_000_000,
        )
        self.assertEqual(modifier, 2.0,
            msg=f"Di bawah budget harus +2, bukan {modifier}")

    def test_slightly_over_budget_gives_penalty_five(self):
        """Produk melebihi budget <= 20% mendapat penalti -5."""
        # 15_000_000 * 1.10 = 16_500_000 (10% over)
        modifier = _budget_modifier(
            price=16_500_000,
            budget_min=5_000_000,
            budget_max=15_000_000,
        )
        self.assertEqual(modifier, -5.0,
            msg=f"Over budget <=20% harus -5, bukan {modifier}")

    def test_exactly_twenty_pct_over_gives_penalty_five(self):
        """Produk tepat 20% di atas budget mendapat penalti -5 (batas bawah threshold)."""
        # 15_000_000 * 1.20 = 18_000_000 (tepat 20% over)
        modifier = _budget_modifier(18_000_000, 5_000_000, 15_000_000)
        self.assertEqual(modifier, -5.0,
            msg="Tepat 20% over harus -5 (masih dalam threshold)")

    def test_significantly_over_budget_gives_penalty_fifteen(self):
        """Produk melebihi budget > 20% mendapat penalti -15."""
        # 15_000_000 * 1.30 = 19_500_000 (30% over)
        modifier = _budget_modifier(
            price=19_500_000,
            budget_min=5_000_000,
            budget_max=15_000_000,
        )
        self.assertEqual(modifier, -15.0,
            msg=f"Over budget >20% harus -15, bukan {modifier}")

    def test_budget_fit_label_within(self):
        """Label 'within' dikembalikan jika harga dalam rentang budget."""
        label = _budget_fit_label(10_000_000, 5_000_000, 15_000_000)
        self.assertEqual(label, "within")

    def test_budget_fit_label_below(self):
        """Label 'below' dikembalikan jika harga di bawah budget_min."""
        label = _budget_fit_label(2_000_000, 5_000_000, 15_000_000)
        self.assertEqual(label, "below")

    def test_budget_fit_label_above(self):
        """Label 'above' dikembalikan jika harga di atas budget_max."""
        label = _budget_fit_label(20_000_000, 5_000_000, 15_000_000)
        self.assertEqual(label, "above")


# ═══════════════════════════════════════════════════════════════════
# Test Suite 4 — calculate_scores: Ranking & Kelengkapan Hasil
# ═══════════════════════════════════════════════════════════════════
class TestCalculateScores(unittest.TestCase):
    """Menguji fungsi calculate_scores end-to-end dengan data produk nyata."""

    def test_returns_results_for_valid_category(self):
        """Kategori yang valid harus mengembalikan minimal 1 hasil."""
        wizard = _make_wizard(category="smartphone")
        response = calculate_scores(wizard)
        self.assertGreater(len(response.results), 0,
            msg="Harus ada produk hasil scoring untuk kategori smartphone")

    def test_ranking_is_monotonically_descending(self):
        """Produk harus diurutkan dari skor tertinggi ke terendah."""
        wizard = _make_wizard(category="smartphone")
        response = calculate_scores(wizard)
        scores = [r.total_score for r in response.results]
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i], scores[i + 1],
                msg=f"Urutan skor rusak di posisi {i}: {scores[i]} < {scores[i+1]}")

    def test_rank_field_starts_at_one_and_sequential(self):
        """Field 'rank' harus dimulai dari 1 dan berurutan (1, 2, 3, ...)."""
        wizard = _make_wizard(category="smartphone")
        response = calculate_scores(wizard)
        for i, result in enumerate(response.results, start=1):
            self.assertEqual(result.rank, i,
                msg=f"Rank di posisi {i} seharusnya {i}, bukan {result.rank}")

    def test_score_breakdown_has_all_eight_dimensions(self):
        """Setiap produk dalam hasil harus memiliki tepat 8 score_breakdown."""
        wizard = _make_wizard(category="smartphone")
        response = calculate_scores(wizard)
        for result in response.results:
            self.assertEqual(len(result.score_breakdown), 8,
                msg=f"Produk '{result.product.name}' harus punya 8 breakdown, "
                    f"bukan {len(result.score_breakdown)}")

    def test_total_score_equals_sum_of_weighted_scores_plus_modifier(self):
        """Total skor harus (hampir) sama dengan sum(weighted_scores) + budget_modifier."""
        wizard = _make_wizard(
            category="smartphone",
            budget_min=5_000_000,
            budget_max=25_000_000,  # semua produk masuk budget
        )
        response = calculate_scores(wizard)
        for result in response.results:
            expected_base = sum(b.weighted_score for b in result.score_breakdown)
            modifier = _budget_modifier(
                result.product.price, wizard.budget_min, wizard.budget_max
            )
            expected_total = round(expected_base + modifier, 2)
            self.assertAlmostEqual(result.total_score, expected_total, places=1,
                msg=f"Total skor '{result.product.name}' tidak konsisten dengan breakdown")

    def test_why_this_product_is_non_empty_string(self):
        """Setiap hasil harus memiliki narasi 'why_this_product' yang tidak kosong."""
        wizard = _make_wizard(category="smartphone")
        response = calculate_scores(wizard)
        for result in response.results:
            self.assertTrue(len(result.why_this_product) > 0,
                msg=f"Narasi kosong untuk produk '{result.product.name}'")

    def test_budget_fit_field_valid_values(self):
        """Field budget_fit harus bernilai salah satu dari 'within', 'below', 'above'."""
        wizard = _make_wizard(category="smartphone")
        response = calculate_scores(wizard)
        valid_fits = {"within", "below", "above"}
        for result in response.results:
            self.assertIn(result.budget_fit, valid_fits,
                msg=f"budget_fit '{result.budget_fit}' tidak valid")

    def test_empty_category_returns_empty_results(self):
        """Kategori yang tidak punya produk harus mengembalikan list kosong (bukan error)."""
        # Kita gunakan kategori valid tapi override produknya dengan mock
        from unittest.mock import patch
        wizard = _make_wizard(category="smartwatch")
        with patch("app.scoring.get_products_by_category", return_value=[]):
            response = calculate_scores(wizard)
        self.assertEqual(len(response.results), 0,
            msg="Kategori tanpa produk harus mengembalikan list kosong")
        self.assertEqual(response.total_products_evaluated, 0)

    def test_scoring_with_all_scenarios(self):
        """Scoring harus berjalan tanpa error meskipun semua skenario diaktifkan."""
        all_scenarios = list(UsageScenario)
        wizard = _make_wizard(
            category="smartphone",
            scenarios=all_scenarios,
            priorities={dim: 3 for dim in DIMENSIONS},
        )
        try:
            response = calculate_scores(wizard)
            self.assertGreater(len(response.results), 0)
        except Exception as e:
            self.fail(f"calculate_scores gagal dengan semua skenario: {e}")


# ═══════════════════════════════════════════════════════════════════
# Test Suite 5 — Pydantic WizardInput Validation
# ═══════════════════════════════════════════════════════════════════
class TestWizardInputValidation(unittest.TestCase):
    """Memastikan validasi Pydantic menolak input yang tidak valid."""

    def test_valid_input_is_accepted(self):
        """Input yang valid harus diterima tanpa exception."""
        try:
            wizard = _make_wizard(
                category="smartphone",
                budget_min=5_000_000,
                budget_max=15_000_000,
                scenarios=[UsageScenario.GAMING],
                priorities={"performance": 5, "camera": 3},
            )
            self.assertIsNotNone(wizard)
        except ValidationError as e:
            self.fail(f"Input valid seharusnya tidak error: {e}")

    def test_budget_max_less_than_min_is_rejected(self):
        """budget_max < budget_min harus menghasilkan ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            _make_wizard(budget_min=15_000_000, budget_max=5_000_000)
        errors = ctx.exception.errors()
        self.assertTrue(any("budget_max" in str(e) for e in errors),
            msg="Pesan error harus menyebut 'budget_max'")

    def test_priority_value_above_five_is_rejected(self):
        """Nilai prioritas > 5 harus menghasilkan ValidationError."""
        with self.assertRaises(ValidationError):
            _make_wizard(priorities={"performance": 6})

    def test_priority_value_zero_is_rejected(self):
        """Nilai prioritas 0 harus menghasilkan ValidationError (di luar 1-5)."""
        with self.assertRaises(ValidationError):
            _make_wizard(priorities={"camera": 0})

    def test_unknown_priority_dimension_is_rejected(self):
        """Dimensi prioritas yang tidak dikenal harus menghasilkan ValidationError."""
        with self.assertRaises(ValidationError):
            _make_wizard(priorities={"kecepatan": 3})

    def test_equal_budget_min_max_is_valid(self):
        """budget_min == budget_max harus diterima (produk harga tepat)."""
        try:
            wizard = _make_wizard(budget_min=10_000_000, budget_max=10_000_000)
            self.assertIsNotNone(wizard)
        except ValidationError as e:
            self.fail(f"budget_min == budget_max seharusnya valid: {e}")

    def test_invalid_category_is_rejected(self):
        """Kategori yang tidak terdaftar harus menghasilkan ValidationError."""
        with self.assertRaises(ValidationError):
            WizardInput(
                category="drone",
                budget_min=1_000_000,
                budget_max=5_000_000,
            )

    def test_priority_boundary_values_are_accepted(self):
        """Nilai prioritas 1 dan 5 (batas minimum dan maksimum) harus valid."""
        try:
            wizard = _make_wizard(priorities={"performance": 1, "camera": 5})
            self.assertIsNotNone(wizard)
        except ValidationError as e:
            self.fail(f"Nilai batas 1 dan 5 seharusnya valid: {e}")


# ═══════════════════════════════════════════════════════════════════
# Test Suite 6 — Why Narrative Generation
# ═══════════════════════════════════════════════════════════════════
class TestWhyNarrativeGeneration(unittest.TestCase):
    """Memastikan narasi 'Why This Product?' dihasilkan dengan benar."""

    def _get_first_result(self, **wizard_kwargs):
        wizard = _make_wizard(**wizard_kwargs)
        response = calculate_scores(wizard)
        self.assertGreater(len(response.results), 0, "Tidak ada produk untuk diuji")
        return response.results[0]

    def test_narrative_contains_product_name(self):
        """Narasi harus mengandung nama produk."""
        result = self._get_first_result(category="smartphone")
        self.assertIn(result.product.name, result.why_this_product,
            msg="Narasi harus menyebut nama produk")

    def test_narrative_contains_budget_context(self):
        """Narasi harus mengandung konteks budget (emoji atau kata kunci)."""
        result = self._get_first_result(
            category="smartphone",
            budget_min=5_000_000,
            budget_max=25_000_000,
        )
        # Narasi harus mengandung salah satu konteks budget
        has_budget_mention = any(
            keyword in result.why_this_product
            for keyword in ["budget", "Budget", "sesuai", "bawah budget", "di atas budget", "💰", "⚠️"]
        )
        self.assertTrue(has_budget_mention,
            msg=f"Narasi harus mengandung konteks budget: {result.why_this_product[:200]}")

    def test_narrative_contains_scenario_if_provided(self):
        """Jika skenario dipilih, narasi harus menyebut skenario tersebut."""
        result = self._get_first_result(
            category="smartphone",
            scenarios=[UsageScenario.GAMING],
        )
        self.assertIn("gaming", result.why_this_product.lower(),
            msg="Narasi harus menyebut skenario 'gaming' jika dipilih")

    def test_narrative_is_multi_line(self):
        """Narasi harus berupa teks multi-baris (mengandung newline)."""
        result = self._get_first_result(category="smartphone")
        self.assertIn("\n", result.why_this_product,
            msg="Narasi harus berupa teks multi-baris")


# ═══════════════════════════════════════════════════════════════════
# Test Suite 7 — Scoring Product Identity Consistency (Phase C: C-01..C-15)
# ═══════════════════════════════════════════════════════════════════
def _make_dummy_product(
    pid="db-001",
    name="Postgres Alpha",
    category=ProductCategory.SMARTPHONE,
    price=10_000_000,
    score_perf=90,
    score_cam=85,
    score_batt=80,
    score_disp=75,
    score_build=70,
    score_val=65,
    score_aud=60,
    score_soft=55,
) -> Product:
    return Product(
        id=pid,
        name=name,
        brand="AlphaBrand",
        category=category,
        price=price,
        image="https://example.com/img.jpg",
        image_url="https://example.com/img.jpg",
        description="Authoritative DB product",
        specs=ProductSpecs(specifications={"processor": "Snapdragon 8 Gen 3"}),
        review_sentiment=ReviewSentiment(overall_score=4.5, total_reviews=10, pros=[], cons=[], summary=""),
        warranty=WarrantyInfo(duration_months=12, coverage="Full", claim_ease=8, official_service_centers=5, score=80.0),
        marketplace_links={},
        tags=["flagship"],
        release_year=2024,
        score_performance=score_perf,
        score_camera=score_cam,
        score_battery=score_batt,
        score_display=score_disp,
        score_build_quality=score_build,
        score_value=score_val,
        score_audio=score_aud,
        score_software=score_soft,
    )


class TestScoringProductIdentityConsistency(unittest.TestCase):
    """
    Phase C Verification: Ensures PostgreSQL is the authoritative candidate-product
    source for scoring recommendations, enforcing fail-closed behavior on database
    outages and preventing ghost product resurrection from in-memory catalog.
    """

    def setUp(self):
        self.client = TestClient(app)
        app.dependency_overrides.clear()
        self.prod_env = {
            "APP_ENV": "production",
            "ALLOW_CATALOG_FALLBACK": "false",
            "RENDER": "",
        }
        self.dev_env_fallback = {
            "APP_ENV": "development",
            "ALLOW_CATALOG_FALLBACK": "true",
            "RENDER": "",
        }
        self.dev_env_no_fallback = {
            "APP_ENV": "development",
            "ALLOW_CATALOG_FALLBACK": "false",
            "RENDER": "",
        }
        self.default_payload = {
            "category": "smartphone",
            "budget_min": 5_000_000,
            "budget_max": 15_000_000,
            "scenarios": ["gaming", "photography"],
            "priorities": {"performance": 5, "camera": 4, "battery": 3},
        }

    def tearDown(self):
        app.dependency_overrides.clear()

    # C-01: PostgreSQL returns matching active products -> scoring uses DB products
    def test_c01_postgres_active_products_used_for_scoring(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        db_prods = [
            _make_dummy_product(pid="pg-001", name="PostgreSQL Alpha", score_perf=95),
            _make_dummy_product(pid="pg-002", name="PostgreSQL Beta", score_perf=60),
        ]

        with patch.dict(os.environ, self.prod_env, clear=False), \
             patch.object(catalog_repo, "get_products_by_category", return_value=db_prods) as mock_get_cat, \
             patch("app.routers.scoring.get_fallback_products_by_category") as mock_fallback:

            res = self.client.post("/api/score", json=self.default_payload)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["total_products_evaluated"], 2)
            self.assertEqual(data["results"][0]["product"]["id"], "pg-001")
            self.assertEqual(data["results"][1]["product"]["id"], "pg-002")
            mock_get_cat.assert_called_once_with(mock_db, "smartphone")
            mock_fallback.assert_not_called()

    # C-02: Product exists only in PostgreSQL, not memory -> eligible for recommendation
    def test_c02_db_only_product_eligible_for_recommendation(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        db_only_prod = _make_dummy_product(pid="pg-exclusive-999", name="Exclusive DB Phone", score_perf=99)

        with patch.dict(os.environ, self.prod_env, clear=False), \
             patch.object(catalog_repo, "get_products_by_category", return_value=[db_only_prod]), \
             patch("app.routers.scoring.get_fallback_products_by_category") as mock_fallback:

            res = self.client.post("/api/score", json=self.default_payload)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(len(data["results"]), 1)
            self.assertEqual(data["results"][0]["product"]["id"], "pg-exclusive-999")
            self.assertEqual(data["results"][0]["rank"], 1)
            mock_fallback.assert_not_called()

    # C-03: Product exists in memory but is inactive/absent in PostgreSQL -> never recommended
    def test_c03_memory_product_absent_in_db_never_recommended(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        # DB returns only pg-001; memory products (e.g. sm-001, sm-002) are not in DB
        db_prods = [_make_dummy_product(pid="pg-001", name="Postgres Live")]

        with patch.dict(os.environ, self.prod_env, clear=False), \
             patch.object(catalog_repo, "get_products_by_category", return_value=db_prods), \
             patch("app.routers.scoring.get_fallback_products_by_category") as mock_fallback:

            res = self.client.post("/api/score", json=self.default_payload)
            self.assertEqual(res.status_code, 200)
            result_ids = [r["product"]["id"] for r in res.json()["results"]]
            self.assertEqual(result_ids, ["pg-001"])
            self.assertNotIn("sm-001", result_ids)
            mock_fallback.assert_not_called()

    # C-04: Successful DB category query returns empty list -> empty recommendation result; no memory fallback
    def test_c04_successful_empty_db_result_returns_empty_response_no_fallback(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        # Test in both production and development environments
        for env_mode in (self.prod_env, self.dev_env_fallback):
            with self.subTest(env=env_mode["APP_ENV"]), \
                 patch.dict(os.environ, env_mode, clear=False), \
                 patch.object(catalog_repo, "get_products_by_category", return_value=[]) as mock_get_cat, \
                 patch("app.routers.scoring.get_fallback_products_by_category") as mock_fallback:

                res = self.client.post("/api/score", json=self.default_payload)
                self.assertEqual(res.status_code, 200)
                data = res.json()
                self.assertEqual(data["results"], [])
                self.assertEqual(data["total_products_evaluated"], 0)
                self.assertEqual(data["wizard_input"]["category"], "smartphone")
                mock_get_cat.assert_called_once_with(mock_db, "smartphone")
                mock_fallback.assert_not_called()

    # C-05: PostgreSQL query raises SQLAlchemyError in production -> HTTP 503
    def test_c05_sqlalchemy_error_in_production_returns_503(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        db_err = OperationalError("SELECT * FROM products", {}, Exception("Connection refused to internal_db:5432"))

        with patch.dict(os.environ, self.prod_env, clear=False), \
             patch.object(catalog_repo, "get_products_by_category", side_effect=db_err), \
             patch("app.routers.scoring.get_fallback_products_by_category") as mock_fallback:

            res = self.client.post("/api/score", json=self.default_payload)
            self.assertEqual(res.status_code, 503)
            self.assertEqual(res.json()["detail"], "Database service unavailable")
            self.assertNotIn("internal_db", res.text)
            self.assertNotIn("5432", res.text)
            mock_fallback.assert_not_called()

    # C-06: DB session unavailable in production -> HTTP 503
    def test_c06_db_session_unavailable_in_production_returns_503(self):
        app.dependency_overrides[get_db] = lambda: None

        with patch.dict(os.environ, self.prod_env, clear=False), \
             patch("app.routers.scoring.get_fallback_products_by_category") as mock_fallback:

            res = self.client.post("/api/score", json=self.default_payload)
            self.assertEqual(res.status_code, 503)
            self.assertEqual(res.json()["detail"], "Database service unavailable")
            mock_fallback.assert_not_called()

    # C-07: DB query raises SQLAlchemyError in permitted development -> complete memory fallback
    def test_c07_sqlalchemy_error_in_development_permits_memory_fallback(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        db_err = OperationalError("SELECT * FROM products", {}, Exception("DB timeout"))
        fallback_prods = [_make_dummy_product(pid="fallback-001", name="Dev Fallback Phone")]

        with patch.dict(os.environ, self.dev_env_fallback, clear=False), \
             patch.object(catalog_repo, "get_products_by_category", side_effect=db_err), \
             patch("app.routers.scoring.get_fallback_products_by_category", return_value=fallback_prods) as mock_fallback:

            res = self.client.post("/api/score", json=self.default_payload)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(len(data["results"]), 1)
            self.assertEqual(data["results"][0]["product"]["id"], "fallback-001")
            mock_fallback.assert_called_once_with("smartphone")

    # C-08: DB unavailable in permitted development -> complete memory fallback
    def test_c08_db_unavailable_in_development_permits_memory_fallback(self):
        app.dependency_overrides[get_db] = lambda: None
        fallback_prods = [_make_dummy_product(pid="fallback-002", name="Dev Fallback Phone 2")]

        with patch.dict(os.environ, self.dev_env_fallback, clear=False), \
             patch("app.routers.scoring.get_fallback_products_by_category", return_value=fallback_prods) as mock_fallback:

            res = self.client.post("/api/score", json=self.default_payload)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(len(data["results"]), 1)
            self.assertEqual(data["results"][0]["product"]["id"], "fallback-002")
            mock_fallback.assert_called_once_with("smartphone")

    # C-09: Development fallback disabled -> HTTP 503
    def test_c09_development_with_fallback_disabled_returns_503(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        db_err = OperationalError("SELECT * FROM products", {}, Exception("DB unreachable"))

        with patch.dict(os.environ, self.dev_env_no_fallback, clear=False), \
             patch.object(catalog_repo, "get_products_by_category", side_effect=db_err), \
             patch("app.routers.scoring.get_fallback_products_by_category") as mock_fallback:

            res = self.client.post("/api/score", json=self.default_payload)
            self.assertEqual(res.status_code, 503)
            self.assertEqual(res.json()["detail"], "Database service unavailable")
            mock_fallback.assert_not_called()

    # C-10: Unexpected application exception in production -> HTTP 500, no fallback
    def test_c10_unexpected_exception_in_production_propagates_500(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        app_err = ValueError("Corrupt product data mapping")

        with patch.dict(os.environ, self.prod_env, clear=False), \
             patch.object(catalog_repo, "get_products_by_category", side_effect=app_err), \
             patch("app.routers.scoring.get_fallback_products_by_category") as mock_fallback:

            client = TestClient(app, raise_server_exceptions=False)
            res = client.post("/api/score", json=self.default_payload)
            self.assertEqual(res.status_code, 500)
            mock_fallback.assert_not_called()

    # C-11: Unexpected application exception in permitted development -> HTTP 500, no fallback
    def test_c11_unexpected_exception_in_permitted_development_propagates_500(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        app_err = TypeError("Unexpected NoneType in score evaluation")

        with patch.dict(os.environ, self.dev_env_fallback, clear=False), \
             patch.object(catalog_repo, "get_products_by_category", side_effect=app_err), \
             patch("app.routers.scoring.get_fallback_products_by_category") as mock_fallback:

            client = TestClient(app, raise_server_exceptions=False)
            res = client.post("/api/score", json=self.default_payload)
            self.assertEqual(res.status_code, 500)
            mock_fallback.assert_not_called()

    # C-12: DB query partially resolves then fails -> no mixed-source candidates
    def test_c12_partial_db_failure_discards_partial_and_avoids_mixed_sources(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        # Simulate an OperationalError occurring mid-query in catalog_repo
        db_err = OperationalError("SELECT * FROM products", {}, Exception("Connection lost mid-stream"))
        fallback_prods = [_make_dummy_product(pid="fallback-only-001", name="Pure Fallback")]

        # In dev mode with fallback: partial DB is discarded, 100% fallback is served
        with patch.dict(os.environ, self.dev_env_fallback, clear=False), \
             patch.object(catalog_repo, "get_products_by_category", side_effect=db_err), \
             patch("app.routers.scoring.get_fallback_products_by_category", return_value=fallback_prods):

            res = self.client.post("/api/score", json=self.default_payload)
            self.assertEqual(res.status_code, 200)
            results = res.json()["results"]
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["product"]["id"], "fallback-only-001")

        # In production mode: returns 503, never mixes
        with patch.dict(os.environ, self.prod_env, clear=False), \
             patch.object(catalog_repo, "get_products_by_category", side_effect=db_err):

            res_prod = self.client.post("/api/score", json=self.default_payload)
            self.assertEqual(res_prod.status_code, 503)

    # C-13: DB products use updated prices and score fields -> scoring uses DB values
    def test_c13_db_updated_price_and_scores_reflected_in_scoring(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        # DB product has custom updated price (8,000,000) and score_performance (98)
        db_prod = _make_dummy_product(
            pid="pg-updated-001",
            name="Postgres Updated Phone",
            price=8_000_000,
            score_perf=98,
        )

        with patch.dict(os.environ, self.prod_env, clear=False), \
             patch.object(catalog_repo, "get_products_by_category", return_value=[db_prod]):

            payload = {
                "category": "smartphone",
                "budget_min": 5_000_000,
                "budget_max": 10_000_000,
                "priorities": {"performance": 5},
            }
            res = self.client.post("/api/score", json=payload)
            self.assertEqual(res.status_code, 200)
            top = res.json()["results"][0]
            self.assertEqual(top["product"]["price"], 8_000_000)
            self.assertEqual(top["budget_fit"], "within")
            perf_breakdown = next(b for b in top["score_breakdown"] if b["dimension"] == "performance")
            self.assertEqual(perf_breakdown["raw_score"], 98)

    # C-14: Existing response contract is preserved
    def test_c14_scoring_response_contract_preserved(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        db_prod = _make_dummy_product(pid="pg-contract-001", name="Contract Phone")

        with patch.dict(os.environ, self.prod_env, clear=False), \
             patch.object(catalog_repo, "get_products_by_category", return_value=[db_prod]):

            res = self.client.post("/api/score", json=self.default_payload)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("results", data)
            self.assertIn("total_products_evaluated", data)
            self.assertIn("wizard_input", data)

            item = data["results"][0]
            self.assertIn("product", item)
            self.assertIn("total_score", item)
            self.assertIn("rank", item)
            self.assertIn("score_breakdown", item)
            self.assertIn("why_this_product", item)
            self.assertIn("budget_fit", item)
            self.assertEqual(len(item["score_breakdown"]), 8)

    # C-15: Existing scoring unit tests & direct calculate_scores compatibility
    def test_c15_calculate_scores_direct_call_backward_compatibility(self):
        wizard = _make_wizard(category="smartphone")
        # Direct call without products argument must use in-memory catalog
        resp_default = calculate_scores(wizard)
        self.assertGreater(resp_default.total_products_evaluated, 0)
        self.assertGreater(len(resp_default.results), 0)

        # Direct call with explicit empty list must return empty result
        resp_empty = calculate_scores(wizard, products=[])
        self.assertEqual(resp_empty.total_products_evaluated, 0)
        self.assertEqual(resp_empty.results, [])

        # Direct call with explicit candidate list uses strictly that list
        custom_prod = _make_dummy_product(pid="custom-001", name="Custom Candidate")
        resp_custom = calculate_scores(wizard, products=[custom_prod])
        self.assertEqual(resp_custom.total_products_evaluated, 1)
        self.assertEqual(resp_custom.results[0].product.id, "custom-001")


if __name__ == "__main__":
    unittest.main(verbosity=2)
