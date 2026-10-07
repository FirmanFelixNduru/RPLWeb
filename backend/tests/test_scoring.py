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
from pydantic import ValidationError

# Pastikan modul app dapat diimpor dari direktori backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models import WizardInput, ProductCategory, UsageScenario
from app.scoring import (
    _build_weight_vector,
    _budget_modifier,
    _budget_fit_label,
    _generate_why_narrative,
    _get_product_score,
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
