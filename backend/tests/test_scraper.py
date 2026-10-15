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
        """Metadata respons sesuai dengan permintaan."""
        with _no_snapshot(), \
             patch.object(scraper, "_scrape_tokopedia", AsyncMock(return_value=None)), \
             patch.object(scraper, "_scrape_shopee", AsyncMock(return_value=None)), \
             patch.object(scraper, "_scrape_lazada", AsyncMock(return_value=None)):
            result = await get_live_prices("sw-001", "Apple Watch Ultra 2")
        self.assertEqual(result.product_id, "sw-001")
        self.assertEqual(result.product_name, "Apple Watch Ultra 2")
        self.assertTrue(result.last_updated.endswith("WIB"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
