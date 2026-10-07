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

from fastapi.testclient import TestClient
from app.main import app
from app.routers.compare import (
    _extract_numeric,
    _higher_is_better,
    _determine_best,
)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
