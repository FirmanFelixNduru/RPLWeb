"""
CompareBuy — Unit Tests: Side-by-Side Comparison Matrix & Auto-Highlighting Engine
Fitur 2 – MVP Version 1

Menguji fungsi-fungsi inti di backend/app/routers/compare.py secara terisolasi
(unit tests) dan via HTTP endpoint (integration tests dengan TestClient).
Menggunakan standar library unittest Python.
"""
import sys
import os
import unittest

# Pastikan modul app dapat diimpor dari direktori backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests import _pretty  # noqa: F401  (format output [OK] ...)

from fastapi.testclient import TestClient
from app.main import app
from app.routers.compare import (
    _extract_numeric,
    _higher_is_better,
    _determine_best,
    _determine_best_with_ties,
)
from app.scoring import calculate_scores
from app.models import WizardInput, ProductCategory, UsageScenario

client = TestClient(app)


# ═══════════════════════════════════════════════════════════════════
# Test Suite 1 — _extract_numeric: Ekstraksi Nilai Numerik
# ═══════════════════════════════════════════════════════════════════
class TestExtractNumeric(unittest.TestCase):
    """Memastikan ekstraksi angka dari string spesifikasi berjalan benar."""

    def test_integer_value(self):
        """Mengekstrak angka bulat dari string sederhana."""
        self.assertEqual(_extract_numeric("12 GB"), 12.0)

    def test_decimal_value(self):
        """Mengekstrak angka desimal dari string."""
        self.assertEqual(_extract_numeric("6.8\" AMOLED"), 6.8)

    def test_value_with_unit_mah(self):
        """Mengekstrak angka dari string kapasitas baterai."""
        self.assertEqual(_extract_numeric("5000 mAh"), 5000.0)

    def test_value_with_unit_mp(self):
        """Mengekstrak angka dari string megapixel kamera."""
        self.assertEqual(_extract_numeric("200MP + 50MP"), 200.0)

    def test_value_with_unit_hz(self):
        """Mengekstrak angka dari string refresh rate."""
        self.assertEqual(_extract_numeric("120Hz Adaptive"), 120.0)

    def test_value_with_commas_stripped(self):
        """Angka dengan pemisah ribuan (koma) harus diekstrak dengan benar."""
        self.assertEqual(_extract_numeric("19,999,000"), 19999000.0)

    def test_weight_with_unit(self):
        """Mengekstrak angka bobot dalam gram."""
        self.assertEqual(_extract_numeric("232g"), 232.0)

    def test_none_input_returns_none(self):
        """Input None harus mengembalikan None."""
        self.assertIsNone(_extract_numeric(None))

    def test_empty_string_returns_none(self):
        """String kosong harus mengembalikan None."""
        self.assertIsNone(_extract_numeric(""))

    def test_na_value_returns_none(self):
        """Nilai 'N/A' harus mengembalikan None."""
        self.assertIsNone(_extract_numeric("N/A"))

    def test_dash_returns_none(self):
        """Karakter '—' (tidak tersedia) harus mengembalikan None."""
        self.assertIsNone(_extract_numeric("—"))

    def test_text_only_returns_none(self):
        """String tanpa angka harus mengembalikan None."""
        self.assertIsNone(_extract_numeric("Titanium Frame"))

    def test_returns_first_number_when_multiple(self):
        """Jika ada banyak angka, harus mengambil angka pertama."""
        # "200MP + 50MP" → 200 (bukan 50)
        result = _extract_numeric("200MP + 50MP")
        self.assertEqual(result, 200.0)


# ═══════════════════════════════════════════════════════════════════
# Test Suite 2 — _higher_is_better: Logika Perbandingan Arah Nilai
# ═══════════════════════════════════════════════════════════════════
class TestHigherIsBetter(unittest.TestCase):
    """Memastikan aturan higher-is-better / lower-is-better per field benar."""

    def test_ram_higher_is_better(self):
        """RAM lebih besar = lebih baik → True."""
        self.assertTrue(_higher_is_better("ram"))

    def test_battery_higher_is_better(self):
        """Baterai lebih besar = lebih baik → True."""
        self.assertTrue(_higher_is_better("battery"))

    def test_camera_higher_is_better(self):
        """Resolusi kamera lebih tinggi = lebih baik → True."""
        self.assertTrue(_higher_is_better("camera"))

    def test_display_higher_is_better(self):
        """Ukuran layar lebih besar = lebih baik → True."""
        self.assertTrue(_higher_is_better("display"))

    def test_refresh_rate_higher_is_better(self):
        """Refresh rate lebih tinggi = lebih baik → True."""
        self.assertTrue(_higher_is_better("refresh_rate"))

    def test_storage_higher_is_better(self):
        """Kapasitas storage lebih besar = lebih baik → True."""
        self.assertTrue(_higher_is_better("storage"))

    def test_weight_lower_is_better(self):
        """Bobot lebih ringan = lebih baik → False."""
        self.assertFalse(_higher_is_better("weight"),
            msg="Field 'weight' harus lower-is-better (False)")

    def test_price_lower_is_better(self):
        """Harga lebih murah = lebih baik untuk pembeli → False.
        
        Ini adalah review dari mahasiswa: price harus diperlakukan
        sebagai lower-is-better, bukan higher-is-better.
        """
        self.assertFalse(_higher_is_better("price"),
            msg="Field 'price' harus lower-is-better (False) — pembeli memilih harga termurah")

    def test_unknown_field_defaults_to_higher_is_better(self):
        """Field yang tidak dikenal harus default ke higher-is-better (True)."""
        self.assertTrue(_higher_is_better("unknown_spec_field"))

    def test_weight_and_price_are_the_only_exceptions(self):
        """Hanya 'weight' dan 'price' yang seharusnya lower-is-better."""
        lower_is_better_fields = ["weight", "price"]
        for field in lower_is_better_fields:
            self.assertFalse(_higher_is_better(field),
                msg=f"Field '{field}' harus lower-is-better")


# ═══════════════════════════════════════════════════════════════════
# Test Suite 3 — _determine_best: Penentuan Produk Terbaik per Spec
# ═══════════════════════════════════════════════════════════════════
class TestDetermineBest(unittest.TestCase):
    """Memastikan penentuan produk terbaik per spesifikasi berjalan benar."""

    def test_selects_highest_ram(self):
        """Produk dengan RAM terbesar harus menjadi pemenang."""
        values = {
            "sm-001": "12 GB",
            "sm-002": "8 GB",
            "sm-003": "16 GB",
        }
        best = _determine_best("ram", values)
        self.assertEqual(best, "sm-003",
            msg="RAM 16 GB harus menjadi pemenang")

    def test_selects_lightest_weight(self):
        """Produk dengan bobot teringan harus menjadi pemenang (lower-is-better)."""
        values = {
            "lp-001": "2.1 kg",
            "lp-002": "1.4 kg",
            "lp-003": "1.8 kg",
        }
        best = _determine_best("weight", values)
        self.assertEqual(best, "lp-002",
            msg="Bobot 1.4 kg (teringan) harus menjadi pemenang")

    def test_selects_cheapest_price(self):
        """Produk dengan harga termurah harus menjadi pemenang (lower-is-better).
        
        Ini memvalidasi review mahasiswa: price harus lower-is-better.
        """
        values = {
            "sm-001": "19999000",
            "sm-002": "22499000",
            "sm-003": "12999000",
        }
        best = _determine_best("price", values)
        self.assertEqual(best, "sm-003",
            msg="Harga Rp 12.999.000 (termurah) harus menjadi pemenang")

    def test_selects_highest_battery(self):
        """Produk dengan baterai terbesar harus menjadi pemenang."""
        values = {
            "sm-001": "5000 mAh",
            "sm-002": "4441 mAh",
        }
        best = _determine_best("battery", values)
        self.assertEqual(best, "sm-001",
            msg="Baterai 5000 mAh harus menjadi pemenang")

    def test_selects_highest_camera_mp(self):
        """Produk dengan resolusi kamera tertinggi harus menjadi pemenang."""
        values = {
            "sm-001": "200MP + 50MP",
            "sm-002": "48MP + 12MP",
            "sm-003": "50MP + 50MP",
        }
        best = _determine_best("camera", values)
        self.assertEqual(best, "sm-001",
            msg="200MP harus menjadi pemenang kamera")

    def test_all_na_values_returns_none(self):
        """Jika semua nilai adalah N/A atau tidak ekstrak, harus mengembalikan None."""
        values = {
            "sm-001": "N/A",
            "sm-002": "—",
            "sm-003": "",
        }
        best = _determine_best("anc", values)
        self.assertIsNone(best,
            msg="Jika tidak ada nilai numerik, harus mengembalikan None")

    def test_single_product_always_wins(self):
        """Jika hanya ada 1 produk dengan nilai numerik, produk itu yang menang."""
        values = {"sm-001": "5000 mAh"}
        best = _determine_best("battery", values)
        self.assertEqual(best, "sm-001")

    def test_mixed_na_and_valid_values(self):
        """Produk dengan N/A diabaikan; pemenang dari produk yang punya nilai numerik."""
        values = {
            "sm-001": "N/A",
            "sm-002": "12 GB",
            "sm-003": "8 GB",
        }
        best = _determine_best("ram", values)
        self.assertEqual(best, "sm-002",
            msg="sm-001 (N/A) harus diabaikan; sm-002 (12 GB) menang")

    def test_tie_broken_deterministically(self):
        """Nilai yang sama — harus mengembalikan salah satu (tidak crash/None)."""
        values = {
            "sm-001": "12 GB",
            "sm-002": "12 GB",
        }
        best = _determine_best("ram", values)
        self.assertIn(best, {"sm-001", "sm-002"},
            msg="Tie harus mengembalikan salah satu ID yang valid, bukan None")


# ═══════════════════════════════════════════════════════════════════
# Test Suite 4 — /api/compare Endpoint (Integration via TestClient)
# ═══════════════════════════════════════════════════════════════════
class TestCompareEndpoint(unittest.TestCase):
    """Menguji endpoint /api/compare secara end-to-end via FastAPI TestClient."""

    def test_compare_two_products_returns_200(self):
        """Perbandingan 2 produk valid harus mengembalikan HTTP 200."""
        res = client.post("/api/compare", json={"product_ids": ["sm-001", "sm-002"]})
        self.assertEqual(res.status_code, 200,
            msg=f"Expected 200, got {res.status_code}: {res.text}")

    def test_compare_two_products_returns_correct_count(self):
        """Respons harus berisi tepat 2 produk."""
        res = client.post("/api/compare", json={"product_ids": ["sm-001", "sm-002"]})
        data = res.json()
        self.assertEqual(len(data["products"]), 2)

    def test_compare_three_products_returns_200(self):
        """Perbandingan 3 produk valid harus mengembalikan HTTP 200."""
        res = client.post("/api/compare", json={"product_ids": ["sm-001", "sm-002", "sm-003"]})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["products"]), 3)

    def test_compare_four_products_returns_200(self):
        """Perbandingan 4 produk (batas maksimum) harus mengembalikan HTTP 200."""
        res = client.post("/api/compare", json={"product_ids": ["sm-001", "sm-002", "sm-003", "sm-004"]})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["products"]), 4)

    def test_compare_five_products_returns_422(self):
        """Lebih dari 4 produk harus ditolak dengan HTTP 422 (Unprocessable Entity)."""
        res = client.post("/api/compare", json={
            "product_ids": ["sm-001", "sm-002", "sm-003", "sm-004", "sm-005"]
        })
        self.assertEqual(res.status_code, 422,
            msg="5 produk harus ditolak (max 4)")

    def test_compare_one_product_returns_422(self):
        """Kurang dari 2 produk harus ditolak dengan HTTP 422."""
        res = client.post("/api/compare", json={"product_ids": ["sm-001"]})
        self.assertEqual(res.status_code, 422,
            msg="1 produk harus ditolak (min 2)")

    def test_compare_duplicate_ids_returns_422(self):
        """ID produk yang duplikat harus ditolak dengan HTTP 422.

        Validasi ditangani oleh Pydantic @field_validator di CompareRequest,
        bukan oleh HTTPException di handler, sehingga status code yang tepat
        adalah 422 (Unprocessable Entity), bukan 400.
        """
        res = client.post("/api/compare", json={"product_ids": ["sm-001", "sm-001"]})
        self.assertEqual(res.status_code, 422,
            msg="ID duplikat harus mengembalikan 422 (Pydantic validation error)")

    def test_compare_missing_product_returns_404(self):
        """ID produk yang tidak ada harus mengembalikan HTTP 404."""
        res = client.post("/api/compare", json={"product_ids": ["sm-001", "tidak-ada"]})
        self.assertEqual(res.status_code, 404,
            msg="Produk tidak ditemukan harus mengembalikan 404")

    def test_compare_response_contains_highlights(self):
        """Respons perbandingan harus mengandung daftar highlights yang tidak kosong."""
        res = client.post("/api/compare", json={"product_ids": ["sm-001", "sm-002"]})
        data = res.json()
        self.assertIn("highlights", data)
        self.assertGreater(len(data["highlights"]), 0,
            msg="Highlights tidak boleh kosong")

    def test_compare_product_ids_in_response_match_request(self):
        """ID produk dalam respons harus sesuai dengan ID yang diminta."""
        requested_ids = ["sm-001", "sm-002"]
        res = client.post("/api/compare", json={"product_ids": requested_ids})
        returned_ids = [p["id"] for p in res.json()["products"]]
        self.assertEqual(sorted(returned_ids), sorted(requested_ids),
            msg="ID produk dalam respons tidak cocok dengan permintaan")


# ═══════════════════════════════════════════════════════════════════
# Test Suite 5 — Struktur & Integritas Highlight Perbandingan
# ═══════════════════════════════════════════════════════════════════
class TestHighlightStructure(unittest.TestCase):
    """Memastikan setiap entri highlight memiliki struktur data yang valid."""

    @classmethod
    def setUpClass(cls):
        """Ambil data perbandingan sekali, dipakai semua test dalam suite ini."""
        res = client.post("/api/compare", json={"product_ids": ["sm-001", "sm-002", "sm-003"]})
        assert res.status_code == 200, f"Setup gagal: {res.status_code} {res.text}"
        cls.data = res.json()
        cls.highlights = cls.data["highlights"]
        cls.product_ids = {p["id"] for p in cls.data["products"]}

    def test_every_highlight_has_spec_name(self):
        """Setiap highlight harus memiliki field 'spec_name' yang tidak kosong."""
        for h in self.highlights:
            self.assertIn("spec_name", h,
                msg=f"Highlight tanpa spec_name: {h}")
            self.assertTrue(len(h["spec_name"]) > 0,
                msg="spec_name tidak boleh string kosong")

    def test_every_highlight_has_values_dict(self):
        """Setiap highlight harus memiliki field 'values' berupa dictionary."""
        for h in self.highlights:
            self.assertIn("values", h,
                msg=f"Highlight tanpa values: {h}")
            self.assertIsInstance(h["values"], dict,
                msg=f"'values' harus berupa dict, bukan {type(h['values'])}")

    def test_every_highlight_has_best_product_id(self):
        """Setiap highlight harus memiliki field 'best_product_id'."""
        for h in self.highlights:
            self.assertIn("best_product_id", h,
                msg=f"Highlight tanpa best_product_id: {h}")

    def test_best_product_id_is_among_compared_products(self):
        """best_product_id harus merupakan salah satu dari ID produk yang dibandingkan,
        atau string kosong (untuk spec yang semua nilainya non-numerik)."""
        for h in self.highlights:
            bpid = h["best_product_id"]
            self.assertTrue(
                bpid in self.product_ids or bpid == "",
                msg=f"best_product_id '{bpid}' tidak ada di produk yang dibandingkan"
            )

    def test_values_keys_cover_all_compared_products(self):
        """dict 'values' pada setiap highlight harus mencakup semua ID produk yang dibandingkan."""
        for h in self.highlights:
            highlight_ids = set(h["values"].keys())
            self.assertEqual(highlight_ids, self.product_ids,
                msg=f"Highlight '{h['spec_name']}' tidak mencakup semua produk: "
                    f"expected {self.product_ids}, got {highlight_ids}")

    def test_spec_names_are_unique(self):
        """Tidak boleh ada spec_name yang duplikat dalam satu respons perbandingan."""
        names = [h["spec_name"] for h in self.highlights]
        self.assertEqual(len(names), len(set(names)),
            msg=f"Ada spec_name duplikat: {[n for n in names if names.count(n) > 1]}")

    def test_price_highlight_exists_and_lower_is_better(self):
        """Highlight 'Harga (IDR)' harus ada dan best_product_id adalah produk termurah."""
        price_highlights = [h for h in self.highlights if h["spec_name"] == "Harga (IDR)"]
        self.assertEqual(len(price_highlights), 1,
            msg="Harus ada tepat 1 highlight 'Harga (IDR)'")

        price_h = price_highlights[0]
        prices = {pid: int(val) for pid, val in price_h["values"].items()}
        cheapest_id = min(prices, key=prices.get)
        self.assertEqual(price_h["best_product_id"], cheapest_id,
            msg=f"best_product_id untuk harga harus '{cheapest_id}' (termurah), "
                f"bukan '{price_h['best_product_id']}'")


# ═══════════════════════════════════════════════════════════════════
# Test Suite 6 — Regresi _extract_numeric: Rupiah, Ribuan, & Kata "Sharp"
# ═══════════════════════════════════════════════════════════════════
class TestExtractNumericRegression(unittest.TestCase):
    """Regresi US-02: format Rupiah, pemisah ribuan titik, dan false-positive 'Rp'."""

    def test_sharp_is_not_treated_as_rupiah(self):
        """Kata 'Sharp' tidak boleh dianggap token Rp; hasilnya 6.8."""
        self.assertEqual(_extract_numeric('Sharp 6.8" Dynamic AMOLED'), 6.8)

    def test_rupiah_with_dot_thousands(self):
        """'Rp 19.999.000' harus menjadi 19999000.0."""
        self.assertEqual(_extract_numeric("Rp 19.999.000"), 19999000.0)

    def test_rupiah_with_dot_after_prefix(self):
        """'Rp. 50.000' harus menjadi 50000.0."""
        self.assertEqual(_extract_numeric("Rp. 50.000"), 50000.0)

    def test_model_number_not_merged_with_thousands(self):
        """Angka model '15' tidak boleh tergabung dengan harga 19.999.000."""
        self.assertEqual(_extract_numeric("Model 15, harga 19.999.000"), 19999000.0)

    def test_version_string_not_treated_as_thousands(self):
        """'Version 1.2.3' bukan format ribuan; angka pertama 1.2 yang diambil."""
        self.assertEqual(_extract_numeric("Version 1.2.3"), 1.2)

    def test_determine_best_price_with_rupiah_strings(self):
        """Harga berformat Rupiah titik: termurah (lower-is-better) harus menang."""
        values = {
            "sm-001": "Rp 19.999.000",
            "sm-002": "Rp 22.499.000",
            "sm-003": "Rp 12.999.000",
        }
        self.assertEqual(_determine_best("price", values), "sm-003")


# ═══════════════════════════════════════════════════════════════════
# Test Suite 7 — Revisi 10: Auto-Highlighting, Win-Count, & Normalisasi
# ═══════════════════════════════════════════════════════════════════
class TestCompareRevision10Features(unittest.TestCase):
    """Pengujian komprehensif fitur Revisi 10 Compare Score & Auto-Highlighting."""

    def test_storage_1tb_beats_512gb(self):
        """Storage 1 TB dinormalisasi menjadi 1024 GB dan mengalahkan 512 GB."""
        self.assertEqual(_extract_numeric("1 TB SSD", "storage"), 1024.0)
        self.assertEqual(_extract_numeric("512 GB SSD", "storage"), 512.0)
        best_id, winners, is_tie = _determine_best_with_ties("storage", {
            "p1": "1 TB NVMe SSD",
            "p2": "512 GB NVMe SSD"
        })
        self.assertEqual(best_id, "p1")
        self.assertEqual(winners, ["p1"])
        self.assertFalse(is_tie)

    def test_weight_kg_vs_g_normalization(self):
        """Bobot 1.4 kg dinormalisasi menjadi 1400 g; 232 g menang karena lower-is-better."""
        self.assertEqual(_extract_numeric("1.4 kg", "weight"), 1400.0)
        self.assertEqual(_extract_numeric("232 g", "weight"), 232.0)
        best_id, winners, is_tie = _determine_best_with_ties("weight", {
            "p_heavy": "1.4 kg",
            "p_light": "232 g"
        })
        self.assertEqual(best_id, "p_light")
        self.assertEqual(winners, ["p_light"])
        self.assertFalse(is_tie)

    def test_descriptive_fields_do_not_extract_arbitrary_numbers(self):
        """Field deskriptif tidak boleh mengekstrak angka acak dari teks."""
        descriptive_cases = [
            ("processor", "Snapdragon 8 Gen 3"),
            ("os", "Windows 11 Home 64-bit"),
            ("ports", "2x Thunderbolt 4, 1x HDMI 2.1"),
            ("build_material", "Titanium frame with Gorilla Glass Victus 2"),
            ("connectivity", "Wi-Fi 7, Bluetooth 5.4"),
            ("special_features", "S-Pen support, IP68 water resistance"),
            ("sensors", "Fingerprint (under display, ultrasonic), accelerometer")
        ]
        for field, text in descriptive_cases:
            self.assertIsNone(_extract_numeric(text, field), f"Field {field} mengekstrak angka dari '{text}'")

        best_id, winners, is_tie = _determine_best_with_ties("processor", {
            "p1": "Intel Core i9 14900HX",
            "p2": "Apple M3 Max"
        })
        self.assertIsNone(best_id)
        self.assertEqual(winners, [])
        self.assertFalse(is_tie)

    def test_incompatible_battery_units_return_none(self):
        """Baterai dengan satuan tidak sepadan (mAh vs Wh) tidak boleh dibandingkan."""
        best_id, winners, is_tie = _determine_best_with_ties("battery", {
            "p_phone": "5000 mAh",
            "p_laptop": "52.6 Wh"
        })
        self.assertIsNone(best_id)
        self.assertEqual(winners, [])
        self.assertFalse(is_tie)

        # Satuan yang sama tetap dapat dibandingkan
        best_mah, _, _ = _determine_best_with_ties("battery", {
            "p1": "5000 mAh",
            "p2": "4500 mAh"
        })
        self.assertEqual(best_mah, "p1")

        best_wh, _, _ = _determine_best_with_ties("battery", {
            "l1": "73 Wh",
            "l2": "90 Wh"
        })
        self.assertEqual(best_wh, "l2")

    def test_empty_and_single_and_zero_values(self):
        """Penanganan nilai kosong, placeholder dash, data tunggal, dan nilai nol."""
        # Semua kosong
        best_id, winners, is_tie = _determine_best_with_ties("storage", {
            "p1": "",
            "p2": "—",
            "p3": "N/A"
        })
        self.assertIsNone(best_id)
        self.assertEqual(winners, [])
        self.assertFalse(is_tie)

        # Satu produk valid, lainnya kosong
        best_id, winners, is_tie = _determine_best_with_ties("storage", {
            "p1": "512 GB",
            "p2": "—",
            "p3": ""
        })
        self.assertEqual(best_id, "p1")
        self.assertEqual(winners, ["p1"])
        self.assertFalse(is_tie)

        # Nilai numerik 0
        self.assertEqual(_extract_numeric("0 GB"), 0.0)

    def test_tie_highlight_and_shared_win(self):
        """Highlight seri: produk dengan nilai tertinggi sama mendapat status tie, best_product_id kosong,
        dan setiap produk seri memperoleh +1 shared win di win-count."""
        best_id, winners, is_tie = _determine_best_with_ties("ram", {
            "p1": "16 GB",
            "p2": "16 GB",
            "p3": "8 GB"
        })
        self.assertTrue(is_tie)
        self.assertEqual(set(winners), {"p1", "p2"})
        self.assertEqual(best_id, "")  # Poin 1: kosongkan saat seri!

        # Uji via endpoint /api/compare untuk produk dengan refresh rate sama (120 Hz)
        res = client.post("/api/compare", json={"product_ids": ["sm-001", "sm-002"]})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        rr_h = next((h for h in data["highlights"] if h["spec_name"] == "refresh_rate"), None)
        if rr_h and len(rr_h["best_product_ids"]) > 1:
            self.assertTrue(rr_h["is_tie"])
            self.assertEqual(rr_h["best_product_id"], "")  # Poin 1: kosongkan saat seri!
            self.assertIn("sm-001", rr_h["best_product_ids"])
            self.assertIn("sm-002", rr_h["best_product_ids"])

        # Uji shared wins pada dimensi kinerja: tw-001 dan tw-002 memiliki score_performance = 70 (seri)
        res_tws = client.post("/api/compare", json={"product_ids": ["tw-001", "tw-002"]})
        self.assertEqual(res_tws.status_code, 200)
        d_tws = res_tws.json()

        perf_h = next((h for h in d_tws["highlights"] if h["spec_name"] == "Skor Performa"), None)
        self.assertIsNotNone(perf_h)
        self.assertTrue(perf_h["is_tie"])
        self.assertEqual(perf_h["best_product_id"], "")
        self.assertEqual(set(perf_h["best_product_ids"]), {"tw-001", "tw-002"})

        # Verifikasi win_summary: kedua produk memperoleh +1 shared win untuk Skor Performa
        w_map = {w["product_id"]: w for w in d_tws["win_summary"]}
        self.assertIn("tw-001", w_map)
        self.assertIn("tw-002", w_map)

        tw1_summary = w_map["tw-001"]
        tw2_summary = w_map["tw-002"]

        self.assertIn("Skor Performa (Seri)", tw1_summary["tied_sectors"])
        self.assertIn("Skor Performa (Seri)", tw2_summary["tied_sectors"])
        self.assertEqual(tw1_summary["shared_wins"], 1)
        self.assertEqual(tw2_summary["shared_wins"], 1)

        # win_count = solo_wins + shared_wins
        self.assertEqual(tw1_summary["win_count"], tw1_summary["solo_wins"] + tw1_summary["shared_wins"])
        self.assertEqual(tw2_summary["win_count"], tw2_summary["solo_wins"] + tw2_summary["shared_wins"])

        # Akumulasi total win_count (4 + 3 = 7) melampaui jumlah 6 sektor fisik unik TWS
        total_wins = tw1_summary["win_count"] + tw2_summary["win_count"]
        self.assertEqual(total_wins, 7)
        self.assertGreater(total_wins, 6)

        # Ringkasan transparan menyebutkan sektor seri
        self.assertTrue(any("Skor Performa: Seri" in s for s in d_tws["tied_sectors_summary"]))

    def test_dimension_relevance_tws(self):
        """Kategori TWS: Kamera dan Layar tidak berlaku ('— (Tidak Berlaku)') dan tidak dihitung win."""
        res = client.post("/api/compare", json={"product_ids": ["tw-001", "tw-002"]})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        dim_h = {h["spec_name"]: h for h in data["highlights"]}

        self.assertIn("Skor Kamera", dim_h)
        self.assertEqual(dim_h["Skor Kamera"]["values"]["tw-001"], "— (Tidak Berlaku)")
        self.assertEqual(dim_h["Skor Kamera"]["best_product_id"], "")
        self.assertEqual(dim_h["Skor Kamera"]["best_product_ids"], [])

        self.assertIn("Skor Layar", dim_h)
        self.assertEqual(dim_h["Skor Layar"]["values"]["tw-001"], "— (Tidak Berlaku)")
        self.assertEqual(dim_h["Skor Layar"]["best_product_id"], "")
        self.assertEqual(dim_h["Skor Layar"]["best_product_ids"], [])

        for summary in data["win_summary"]:
            self.assertNotIn("Skor Kamera", summary["winning_sectors"])
            self.assertNotIn("Skor Layar", summary["winning_sectors"])

    def test_dimension_relevance_smartwatch(self):
        """Kategori Smartwatch: Kamera tidak berlaku, namun Layar tetap berlaku."""
        res = client.post("/api/compare", json={"product_ids": ["sw-001", "sw-002"]})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        dim_h = {h["spec_name"]: h for h in data["highlights"]}

        self.assertIn("Skor Kamera", dim_h)
        self.assertEqual(dim_h["Skor Kamera"]["values"]["sw-001"], "— (Tidak Berlaku)")
        self.assertEqual(dim_h["Skor Kamera"]["best_product_id"], "")
        self.assertEqual(dim_h["Skor Kamera"]["best_product_ids"], [])

        self.assertIn("Skor Layar", dim_h)
        self.assertNotEqual(dim_h["Skor Layar"]["values"]["sw-001"], "— (Tidak Berlaku)")

    def test_cross_category_comparison_no_universal_winner(self):
        """Komparasi lintas kategori: tidak ada pemenang universal dan win_summary kosong."""
        res = client.post("/api/compare", json={"product_ids": ["lp-001", "sm-001"]})
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertFalse(data["is_same_category"])
        self.assertEqual(data["win_summary"], [])

        for h in data["highlights"]:
            if h["spec_name"].startswith("Skor "):
                self.assertEqual(h["best_product_id"], "")
                self.assertEqual(h["best_product_ids"], [])

    def test_price_cross_category_and_verification_rules(self):
        """Komparasi lintas kategori tidak boleh menetapkan pemenang harga universal; data varian tetap utuh."""
        res = client.post("/api/compare", json={"product_ids": ["lp-001", "sm-001"]})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        price_h = next((h for h in data["highlights"] if h["spec_name"] == "Harga (IDR)"), None)
        self.assertIsNotNone(price_h)
        self.assertEqual(price_h["best_product_id"], "")
        self.assertEqual(price_h["best_product_ids"], [])

    def test_price_tie_clears_best_product_id(self):
        """Poin 1: Seri harga (sm-003 & sm-004 @ Rp 14.999.000) mengosongkan best_product_id dan mengisi best_product_ids."""
        res = client.post("/api/compare", json={"product_ids": ["sm-003", "sm-004"]})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        price_h = next((h for h in data["highlights"] if h["spec_name"] == "Harga (IDR)"), None)
        self.assertIsNotNone(price_h)
        self.assertTrue(price_h["is_tie"])
        self.assertEqual(price_h["best_product_id"], "")
        self.assertEqual(set(price_h["best_product_ids"]), {"sm-003", "sm-004"})

    def test_price_eligibility_and_configuration_comparability(self):
        """Poin 3: Verifikasi bahwa harga tidak mendapat highlight termurah bila unverified atau konfigurasi berbeda."""
        import subprocess
        import json
        node_script = """
        const fs = require('fs');
        const content = fs.readFileSync('frontend/src/components/compare/ComparisonMatrix.js', 'utf8');
        const match = content.match(/export function checkPriceHighlightEligibility[\\s\\S]*?\\n\\}/);
        if (!match) throw new Error("checkPriceHighlightEligibility not found");
        eval(match[0].replace('export function', 'function'));

        const results = {
            unverified_acer: checkPriceHighlightEligibility([
                { id: 'lp-004', price: 8499000, specs: { base_configuration: '8 GB RAM', variants_note: 'belum terverifikasi' } },
                { id: 'lp-001', price: 29999000, specs: { base_configuration: '32 GB RAM' } }
            ], true),
            import_pixel: checkPriceHighlightEligibility([
                { id: 'sm-003', price: 14999000, specs: { base_configuration: '12 GB RAM / 128 GB' }, warranty: { warranty_type: 'impor non-ATPM' } },
                { id: 'sm-001', price: 21999000, specs: { base_configuration: '12 GB RAM / 256 GB' } }
            ], true),
            diff_ram: checkPriceHighlightEligibility([
                { id: 'p1', price: 10000000, specs: { base_configuration: '8 GB RAM / 256 GB' } },
                { id: 'p2', price: 15000000, specs: { base_configuration: '16 GB RAM / 256 GB' } }
            ], true),
            diff_storage: checkPriceHighlightEligibility([
                { id: 'p1', price: 10000000, specs: { base_configuration: '16 GB RAM / 256 GB' } },
                { id: 'p2', price: 15000000, specs: { base_configuration: '16 GB RAM / 512 GB' } }
            ], true),
            cross_cat: checkPriceHighlightEligibility([
                { id: 'p1', price: 10000000, specs: { base_configuration: '16 GB RAM / 256 GB' } },
                { id: 'p2', price: 2000000, specs: { base_configuration: '16 GB RAM / 256 GB' } }
            ], false),
            comparable: checkPriceHighlightEligibility([
                { id: 'lp-005', price: 13999000, specs: { base_configuration: '16 GB RAM / 512 GB' } },
                { id: 'lp-003', price: 24999000, specs: { base_configuration: '16 GB RAM / 512 GB' } }
            ], true)
        };
        console.log(JSON.stringify(results));
        """
        proc = subprocess.run(
            ["node", "-e", node_script],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), "..", "..")
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        data = json.loads(proc.stdout)
        self.assertFalse(data["unverified_acer"]["eligible"], "Acer unverified tidak boleh eligible")
        self.assertFalse(data["import_pixel"]["eligible"], "Pixel impor tidak boleh eligible")
        self.assertFalse(data["diff_ram"]["eligible"], "RAM berbeda tidak boleh eligible")
        self.assertFalse(data["diff_storage"]["eligible"], "Storage berbeda tidak boleh eligible")
        self.assertFalse(data["cross_cat"]["eligible"], "Lintas kategori tidak boleh eligible")
        self.assertTrue(data["comparable"]["eligible"], "Konfigurasi identik dan terverifikasi harus eligible")

    def test_warranty_unverified_scope_integrity(self):
        """Produk dengan garansi unverified (lp-002 ASUS ROG) tidak boleh memenangkan highlight garansi sepihak."""
        res = client.post("/api/compare", json={"product_ids": ["lp-001", "lp-002"]})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        warranty_h = next((h for h in data["highlights"] if h["spec_name"] == "Garansi"), None)
        if warranty_h:
            self.assertNotEqual(warranty_h["best_product_id"], "lp-002")

    def test_smart_wizard_non_regression(self):
        """Smart Wizard non-regression: perhitungan skor MCDA tetap utuh dan berfungsi normal."""
        wizard = WizardInput(
            category=ProductCategory.SMARTPHONE,
            budget_min=5000000,
            budget_max=15000000,
            scenarios=[UsageScenario.GAMING],
            priorities={"performance": 5, "battery": 4}
        )
        response = calculate_scores(wizard)
        self.assertGreater(len(response.results), 0)
        self.assertGreater(response.results[0].total_score, 0)
        self.assertIn("skor tinggi karena:", response.results[0].why_this_product)


if __name__ == "__main__":
    unittest.main(verbosity=2)



