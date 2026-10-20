"""
CompareBuy — Unit Tests: Resilient Marketplace Price Monitoring & Fallback Engine
Fitur 4 – MVP Version 1

Menguji backend/app/scraper.py secara terisolasi. Seluruh akses jaringan dan
penyimpanan snapshot database di-mock sehingga tes deterministik dan offline.
Menggunakan standar library unittest Python.
"""
import sys
import os
import unittest
import logging
from unittest.mock import AsyncMock, patch

# Pastikan modul app dapat diimpor dari direktori backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests import _pretty  # noqa: F401  (format output [OK] ...)

import httpx
from app.models import MarketplacePrice
from app import scraper
from app.scraper import (
    FALLBACK_PRICES,
    get_live_prices,
    is_valid_marketplace_url,
)

ACTUAL_PRODUCT_IDS = (
    [f"sm-00{i}" for i in range(1, 7)]
    + [f"lp-00{i}" for i in range(1, 6)]
    + [f"tb-00{i}" for i in range(1, 3)]
    + [f"tw-00{i}" for i in range(1, 5)]
    + [f"sw-00{i}" for i in range(1, 4)]
)


def setUpModule():
    """Bungkam log kegagalan scraping yang disengaja agar output tes tetap bersih."""
    logging.disable(logging.CRITICAL)


def tearDownModule():
    logging.disable(logging.NOTSET)


def _scraped_price(marketplace: str, price: int, url: str) -> MarketplacePrice:
    return MarketplacePrice(
        marketplace=marketplace,
        price=price,
        url=url,
        seller=f"{marketplace} Seller",
        available=True,
        source="scraped",
    )


def _no_snapshot():
    """Cegah penulisan snapshot ke database sungguhan selama tes."""
    return patch("app.repositories.price_repo.save_price_snapshot", return_value=False)


# ═══════════════════════════════════════════════════════════════════
# Test Suite 1 — is_valid_marketplace_url
# ═══════════════════════════════════════════════════════════════════
class TestIsValidMarketplaceUrl(unittest.TestCase):
    """Validasi skema http/https dan hostname resmi marketplace."""

    def test_accepts_official_tokopedia(self):
        """URL resmi Tokopedia diterima."""
        self.assertTrue(is_valid_marketplace_url("https://www.tokopedia.com/search?q=a"))

    def test_accepts_official_shopee(self):
        """URL resmi Shopee diterima."""
        self.assertTrue(is_valid_marketplace_url("https://shopee.co.id/search?keyword=a"))

    def test_accepts_official_lazada(self):
        """URL resmi Lazada diterima."""
        self.assertTrue(is_valid_marketplace_url("https://www.lazada.co.id/catalog/?q=a"))

    def test_accepts_plain_http_scheme(self):
        """Skema http (selain https) diterima."""
        self.assertTrue(is_valid_marketplace_url("http://tokopedia.com/p"))

    def test_accepts_legitimate_subdomain(self):
        """Subdomain sah dari domain resmi diterima."""
        self.assertTrue(is_valid_marketplace_url("https://seller.shopee.co.id/x"))

    def test_rejects_prefix_spoofing(self):
        """Domain spoofing awalan (evil-tokopedia.com) ditolak."""
        self.assertFalse(is_valid_marketplace_url("https://evil-tokopedia.com/search"))

    def test_rejects_suffix_spoofing(self):
        """Domain spoofing akhiran (tokopedia.com.evil.org) ditolak."""
        self.assertFalse(is_valid_marketplace_url("https://tokopedia.com.evil.org/search"))

    def test_rejects_swapped_marketplace_domain(self):
        """Domain marketplace tertukar ditolak."""
        self.assertFalse(is_valid_marketplace_url("https://tokopedia.co.id/search"))
        self.assertFalse(is_valid_marketplace_url("https://shopee.com/search"))

    def test_rejects_ftp_scheme(self):
        """Skema ftp ditolak."""
        self.assertFalse(is_valid_marketplace_url("ftp://www.tokopedia.com/file"))

    def test_rejects_userinfo_spoofing(self):
        """Spoofing lewat userinfo (tokopedia.com@evil.org) ditolak."""
        self.assertFalse(is_valid_marketplace_url("https://tokopedia.com@evil.org/"))

    def test_rejects_empty_and_schemeless_urls(self):
        """URL kosong atau tanpa skema ditolak."""
        self.assertFalse(is_valid_marketplace_url(""))
        self.assertFalse(is_valid_marketplace_url("www.tokopedia.com/search"))


# ═══════════════════════════════════════════════════════════════════
# Test Suite 2 — Data Fallback 20 Produk Aktual
# ═══════════════════════════════════════════════════════════════════
class TestFallbackData(unittest.TestCase):
    """Setiap produk aktual memiliki >= 3 penawaran fallback valid."""

    def test_fallback_covers_all_20_actual_products(self):
        """Data fallback tersedia untuk seluruh 20 produk aktual."""
        self.assertEqual(len(ACTUAL_PRODUCT_IDS), 20)
        for pid in ACTUAL_PRODUCT_IDS:
            self.assertIn(pid, FALLBACK_PRICES, msg=f"Fallback hilang untuk {pid}")

    def test_each_product_has_at_least_three_offers(self):
        """Setiap produk punya minimal 3 penawaran fallback."""
        for pid in ACTUAL_PRODUCT_IDS:
            self.assertGreaterEqual(len(FALLBACK_PRICES[pid]), 3, msg=pid)

    def test_each_product_covers_three_marketplaces(self):
        """Setiap produk mencakup Tokopedia, Shopee, dan Lazada."""
        for pid in ACTUAL_PRODUCT_IDS:
            names = {o.marketplace for o in FALLBACK_PRICES[pid]}
            self.assertTrue({"Tokopedia", "Shopee", "Lazada"} <= names, msg=pid)

    def test_fallback_prices_positive_and_labelled_fallback(self):
        """Harga fallback positif dan berlabel source fallback."""
        for pid in ACTUAL_PRODUCT_IDS:
            for offer in FALLBACK_PRICES[pid]:
                self.assertGreater(offer.price, 0, msg=pid)
                self.assertEqual(offer.source, "fallback", msg=pid)

    def test_fallback_urls_are_official_marketplace_urls(self):
        """Seluruh URL fallback valid dan berasal dari domain resmi."""
        for pid in ACTUAL_PRODUCT_IDS:
            for offer in FALLBACK_PRICES[pid]:
                self.assertTrue(
                    is_valid_marketplace_url(str(offer.url)),
                    msg=f"URL tidak valid untuk {pid}: {offer.url}",
                )


# ═══════════════════════════════════════════════════════════════════
# Test Suite 3 — get_live_prices: Label Sumber & Isolasi Kegagalan
# ═══════════════════════════════════════════════════════════════════
class TestGetLivePrices(unittest.IsolatedAsyncioTestCase):
    """Label scraped vs fallback dan graceful fallback saat jaringan gagal."""

    async def test_all_scrapers_fail_returns_three_fallback_prices(self):
        """Semua scraper gagal menghasilkan 3 harga fallback."""
        with _no_snapshot(), \
             patch.object(scraper, "_scrape_tokopedia", AsyncMock(return_value=None)), \
             patch.object(scraper, "_scrape_shopee", AsyncMock(return_value=None)), \
             patch.object(scraper, "_scrape_lazada", AsyncMock(return_value=None)):
            result = await get_live_prices("sm-001", "Samsung Galaxy S24 Ultra")
        self.assertEqual(len(result.prices), 3)
        self.assertTrue(all(p.source == "fallback" for p in result.prices))

    async def test_successful_scrape_is_labelled_scraped(self):
        """Hasil scrape berhasil berlabel scraped, sisanya fallback."""
        scraped = _scraped_price(
            "Tokopedia", 19000000, "https://www.tokopedia.com/search?q=samsung"
        )
        with _no_snapshot(), \
             patch.object(scraper, "_scrape_tokopedia", AsyncMock(return_value=scraped)), \
             patch.object(scraper, "_scrape_shopee", AsyncMock(return_value=None)), \
             patch.object(scraper, "_scrape_lazada", AsyncMock(return_value=None)):
            result = await get_live_prices("sm-001", "Samsung Galaxy S24 Ultra")
        by_market = {p.marketplace: p for p in result.prices}
        self.assertEqual(by_market["Tokopedia"].source, "scraped")
        self.assertEqual(by_market["Tokopedia"].price, 19000000)
        self.assertEqual(by_market["Shopee"].source, "fallback")
        self.assertEqual(by_market["Lazada"].source, "fallback")
        self.assertEqual(len(result.prices), 3)

    async def test_timeout_exception_falls_back_without_error(self):
        """Timeout jaringan jatuh ke fallback tanpa error."""
        with _no_snapshot(), patch(
            "httpx.AsyncClient.get",
            AsyncMock(side_effect=httpx.TimeoutException("timeout")),
        ):
            result = await get_live_prices("lp-001", "MacBook Air M3")
        self.assertEqual(len(result.prices), 3)
        self.assertTrue(all(p.source == "fallback" for p in result.prices))

    async def test_connect_error_falls_back_without_error(self):
        """ConnectError jatuh ke fallback tanpa error."""
        with _no_snapshot(), patch(
            "httpx.AsyncClient.get",
            AsyncMock(side_effect=httpx.ConnectError("connect failed")),
        ):
            result = await get_live_prices("tw-001", "AirPods Pro 2")
        self.assertEqual(len(result.prices), 3)
        self.assertTrue(all(p.source == "fallback" for p in result.prices))

    async def test_raised_exception_in_one_scraper_is_isolated(self):
        """asyncio.gather(return_exceptions=True): satu scraper error tidak menggagalkan semua."""
        scraped = _scraped_price(
            "Lazada", 18000000, "https://www.lazada.co.id/catalog/?q=macbook"
        )
        with _no_snapshot(), \
             patch.object(scraper, "_scrape_tokopedia", AsyncMock(side_effect=RuntimeError("boom"))), \
             patch.object(scraper, "_scrape_shopee", AsyncMock(side_effect=RuntimeError("boom"))), \
             patch.object(scraper, "_scrape_lazada", AsyncMock(return_value=scraped)):
            result = await get_live_prices("lp-001", "MacBook Air M3")
        by_market = {p.marketplace: p.source for p in result.prices}
        self.assertEqual(
            by_market,
            {"Tokopedia": "fallback", "Shopee": "fallback", "Lazada": "scraped"},
        )

    async def test_prices_sorted_ascending(self):
        """Daftar harga terurut dari termurah."""
        with _no_snapshot(), \
             patch.object(scraper, "_scrape_tokopedia", AsyncMock(return_value=None)), \
             patch.object(scraper, "_scrape_shopee", AsyncMock(return_value=None)), \
             patch.object(scraper, "_scrape_lazada", AsyncMock(return_value=None)):
            result = await get_live_prices("sm-002", "iPhone 15 Pro Max")
        prices = [p.price for p in result.prices]
        self.assertEqual(prices, sorted(prices))

    async def test_response_metadata_matches_request(self):
        """Metadata respons sesuai dengan permintaan, jujur menandai fallback vs live scraped."""
        # 1. Kasus fallback murni: last_updated menandai data referensi dan captured_at is None
        with _no_snapshot(), \
             patch.object(scraper, "_scrape_tokopedia", AsyncMock(return_value=None)), \
             patch.object(scraper, "_scrape_shopee", AsyncMock(return_value=None)), \
             patch.object(scraper, "_scrape_lazada", AsyncMock(return_value=None)):
            result = await get_live_prices("sw-001", "Apple Watch Ultra 2")
        self.assertEqual(result.product_id, "sw-001")
        self.assertEqual(result.product_name, "Apple Watch Ultra 2")
        self.assertEqual(result.last_updated, "Data acuan fallback (Belum diverifikasi live)")
        for p in result.prices:
            self.assertIsNone(p.captured_at, msg="Fallback offer harus memiliki captured_at: None")

        # 2. Kasus ada data scraped sungguhan: last_updated berakhiran WIB
        scraped = _scraped_price("Tokopedia", 15500000, "https://www.tokopedia.com/search?q=apple+watch+ultra+2")
        with _no_snapshot(), \
             patch.object(scraper, "_scrape_tokopedia", AsyncMock(return_value=scraped)), \
             patch.object(scraper, "_scrape_shopee", AsyncMock(return_value=None)), \
             patch.object(scraper, "_scrape_lazada", AsyncMock(return_value=None)):
            scraped_result = await get_live_prices("sw-001", "Apple Watch Ultra 2")
        self.assertTrue(scraped_result.last_updated.endswith("WIB"))


# ═══════════════════════════════════════════════════════════════════
# Test Suite 4 — Robust Price Parser & Rejection (Revisi 5)
# ═══════════════════════════════════════════════════════════════════
class TestPriceParser(unittest.TestCase):
    """Pengujian parser harga: normalisasi Rupiah, penolakan cicilan, penanganan rentang, dan filter aksesoris."""

    def test_parse_standard_rupiah_formats(self):
        """Format standar Rp, titik ribuan, atau koma desimal diparsing dengan benar."""
        from app.scraper import parse_marketplace_price
        self.assertEqual(parse_marketplace_price("Rp 21.999.000"), 21999000)
        self.assertEqual(parse_marketplace_price("Rp21999000"), 21999000)
        self.assertEqual(parse_marketplace_price("21.999.000"), 21999000)
        self.assertEqual(parse_marketplace_price("Rp 4.999.000,00"), 4999000)
        self.assertEqual(parse_marketplace_price("IDR 6.499.000"), 6499000)

    def test_parse_price_range_takes_lower_bound(self):
        """Rentang harga mengambil batas bawah yang valid."""
        from app.scraper import parse_marketplace_price
        self.assertEqual(parse_marketplace_price("Rp 4.500.000 - Rp 5.000.000"), 4500000)
        self.assertEqual(parse_marketplace_price("3.500.000 - 4.000.000"), 3500000)

    def test_reject_installments(self):
        """Format cicilan bulanan ditolak demi mencegah misleading low price."""
        from app.scraper import parse_marketplace_price
        self.assertIsNone(parse_marketplace_price("Rp 1.500.000 / bln"))
        self.assertIsNone(parse_marketplace_price("Rp 500.000 /bulan"))
        self.assertIsNone(parse_marketplace_price("Cicilan Rp 350.000 / bln"))
        self.assertIsNone(parse_marketplace_price("Rp 1.200.000/bln"))

    def test_reject_irrelevant_accessories_in_title(self):
        """Aksesoris seperti casing, kabel, strap, tempered glass ditolak saat validasi judul."""
        from app.scraper import parse_marketplace_price
        # Judul aksesoris ditolak
        self.assertIsNone(parse_marketplace_price("Rp 150.000", title="Casing Silicone Samsung S24 Ultra"))
        self.assertIsNone(parse_marketplace_price("Rp 85.000", title="Tempered Glass iPhone 15 Pro Max"))
        self.assertIsNone(parse_marketplace_price("Rp 250.000", title="Strap Apple Watch Ultra 2 Trail Loop"))
        self.assertIsNone(parse_marketplace_price("Rp 99.000", title="Kabel Charger Type C to C 60W"))
        # Judul produk perangkat utama diterima
        self.assertEqual(
            parse_marketplace_price("Rp 21.999.000", title="Samsung Galaxy S24 Ultra 12/256GB Garansi Resmi"),
            21999000
        )

    def test_reject_out_of_bounds_prices(self):
        """Harga di luar batas wajar (< 50.000 atau > 150.000.000) ditolak."""
        from app.scraper import parse_marketplace_price
        self.assertIsNone(parse_marketplace_price("Rp 15.000"))
        self.assertIsNone(parse_marketplace_price("Rp 250.000.000"))

    def test_invalid_and_empty_inputs(self):
        """Input kosong atau bukan angka menghasilkan None."""
        from app.scraper import parse_marketplace_price
        self.assertIsNone(parse_marketplace_price(""))
        self.assertIsNone(parse_marketplace_price(None))
        self.assertIsNone(parse_marketplace_price("Stok Habis"))


# ═══════════════════════════════════════════════════════════════════
# Test Suite 5 — Determinisme Fallback Tanpa Random Variation (Revisi 5)
# ═══════════════════════════════════════════════════════════════════
class TestFallbackDeterminism(unittest.IsolatedAsyncioTestCase):
    """Memastikan harga fallback tidak lagi menggunakan variasi acak (random.randint)."""

    async def test_fallback_prices_are_strictly_deterministic(self):
        """Panggilan berulang ke get_live_prices saat fallback selalu menghasilkan harga identik."""
        with _no_snapshot(), \
             patch.object(scraper, "_scrape_tokopedia", AsyncMock(return_value=None)), \
             patch.object(scraper, "_scrape_shopee", AsyncMock(return_value=None)), \
             patch.object(scraper, "_scrape_lazada", AsyncMock(return_value=None)):
            
            run1 = await get_live_prices("sm-001", "Samsung Galaxy S24 Ultra")
            run2 = await get_live_prices("sm-001", "Samsung Galaxy S24 Ultra")
            run3 = await get_live_prices("sm-001", "Samsung Galaxy S24 Ultra")

        prices1 = [(p.marketplace, p.price) for p in run1.prices]
        prices2 = [(p.marketplace, p.price) for p in run2.prices]
        prices3 = [(p.marketplace, p.price) for p in run3.prices]

        self.assertEqual(prices1, prices2)
        self.assertEqual(prices2, prices3)



if __name__ == "__main__":
    unittest.main(verbosity=2)
