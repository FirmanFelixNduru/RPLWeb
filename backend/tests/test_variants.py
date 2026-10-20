"""
CompareBuy — Test Suite: Revisi 7 Variant Configuration Integrity
Verifies base_configuration, variants_note, target_configuration,
consistency between backend and frontend, and API payload integrity.
"""
import unittest
import re
import os
from fastapi.testclient import TestClient

from app.main import app
from app.products import PRODUCTS, get_product_by_id
from app.scraper import FALLBACK_PRICES


class TestVariantsIntegrity(unittest.TestCase):
    """Test variant configuration fields, consistency, and API responses."""

    def setUp(self):
        self.client = TestClient(app)

    def test_all_20_products_have_base_configuration_and_note(self):
        """Every single product in backend catalog must have base_configuration and variants_note."""
        self.assertEqual(len(PRODUCTS), 20, "Catalog must contain exactly 20 products")
        for p in PRODUCTS:
            self.assertIsNotNone(p.specs.base_configuration, f"Product {p.id} missing base_configuration")
            self.assertTrue(len(p.specs.base_configuration.strip()) > 0, f"Product {p.id} has empty base_configuration")
            self.assertIsNotNone(p.specs.variants_note, f"Product {p.id} missing variants_note")
            self.assertTrue(len(p.specs.variants_note.strip()) > 0, f"Product {p.id} has empty variants_note")

    def test_acer_aspire_lp004_spec_integrity(self):
        """lp-004 Acer Aspire 5 must explicitly associate price Rp 8.499.000 with RAM 8 GB and note 16 GB is unverified."""
        p = get_product_by_id("lp-004")
        self.assertIsNotNone(p)
        self.assertEqual(p.price, 8499000)
        self.assertIn("8 GB", p.specs.base_configuration)
        self.assertIn("512 GB", p.specs.base_configuration)
        self.assertIn("16 GB", p.specs.variants_note)
        self.assertIn("belum terverifikasi", p.specs.variants_note.lower())

    def test_thinkpad_lp003_spec_integrity(self):
        """lp-003 ThinkPad X1 Carbon Gen 11 must associate price with 16 GB / 512 GB baseline."""
        p = get_product_by_id("lp-003")
        self.assertIsNotNone(p)
        self.assertEqual(p.price, 24999000)
        self.assertIn("16 GB", p.specs.base_configuration)
        self.assertIn("512 GB", p.specs.base_configuration)
        self.assertNotIn("1 TB", p.specs.base_configuration)
        self.assertIn("32 GB", p.specs.variants_note)

    def test_lenovo_loq_lp005_spec_integrity(self):
        """lp-005 Lenovo LOQ must associate price Rp 13.999.000 with 16 GB DDR5 / 512 GB SSD."""
        p = get_product_by_id("lp-005")
        self.assertIsNotNone(p)
        self.assertEqual(p.price, 13999000)
        self.assertIn("16 GB", p.specs.base_configuration)
        self.assertIn("512 GB", p.specs.base_configuration)
        self.assertNotIn("12 GB RAM", p.specs.base_configuration)

    def test_xiaomi_14_ultra_sm004_spec_integrity(self):
        """sm-004 Xiaomi 14 Ultra price must remain Rp 14.999.000 for 16 GB / 512 GB UFS 4.0."""
        p = get_product_by_id("sm-004")
        self.assertIsNotNone(p)
        self.assertEqual(p.price, 14999000)
        self.assertIn("16 GB", p.specs.base_configuration)
        self.assertIn("512 GB", p.specs.base_configuration)
        self.assertIn("UFS 4.0", p.specs.base_configuration)

    def test_fallback_prices_target_configuration_present(self):
        """All entries in FALLBACK_PRICES must specify target_configuration matching simulation baseline."""
        self.assertEqual(len(FALLBACK_PRICES), 20)
        for pid, offers in FALLBACK_PRICES.items():
            self.assertTrue(len(offers) >= 3, f"Product {pid} must have at least 3 fallback offers")
            p = get_product_by_id(pid)
            for offer in offers:
                self.assertIsNotNone(offer.target_configuration, f"Offer for {pid} missing target_configuration")
                self.assertTrue(offer.target_configuration.startswith("Acuan Simulasi:"))
                self.assertIn(p.specs.base_configuration, offer.target_configuration)

    def test_backend_frontend_data_consistency(self):
        """Verify frontend/src/data/products.js matches backend/app/products.py exactly."""
        frontend_path = os.path.join("..", "frontend", "src", "data", "products.js")
        if not os.path.exists(frontend_path):
            self.skipTest("Frontend path not found from current directory")

        with open(frontend_path, "r", encoding="utf-8") as f:
            fe_content = f.read()

        for p in PRODUCTS:
            # Check base_configuration present in frontend
            self.assertIn(p.specs.base_configuration, fe_content, f"Frontend missing base_configuration for {p.id}")

    def test_api_catalog_payload_includes_variant_fields(self):
        """GET /api/products and GET /api/products/{id} must serialize base_configuration and variants_note."""
        resp = self.client.get("/api/products?per_page=20")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        items = data.get("products", [])
        self.assertEqual(len(items), 20)

        for item in items:
            specs = item.get("specs", {})
            self.assertIn("base_configuration", specs, f"Catalog item {item['id']} missing base_configuration in specs")
            self.assertIsNotNone(specs["base_configuration"])
            self.assertIn("variants_note", specs, f"Catalog item {item['id']} missing variants_note in specs")
            self.assertIsNotNone(specs["variants_note"])

        # Test single product endpoint
        detail_resp = self.client.get("/api/products/lp-004")
        self.assertEqual(detail_resp.status_code, 200)
        detail = detail_resp.json()
        self.assertEqual(detail["specs"]["base_configuration"], "Intel Core i5-1335U / 8 GB LPDDR5 / 512 GB SSD PCIe Gen4")

    def test_api_live_prices_payload_includes_target_configuration(self):
        """GET /api/prices/{product_id} must include target_configuration on fallback items."""
        resp = self.client.get("/api/prices/lp-004")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        prices = data.get("prices", [])
        self.assertTrue(len(prices) >= 3)
        for item in prices:
            if item.get("source") == "fallback":
                self.assertIn("target_configuration", item)
                self.assertIsNotNone(item["target_configuration"])
                self.assertTrue(item["target_configuration"].startswith("Acuan Simulasi:"))


if __name__ == "__main__":
    unittest.main()
