"""
CompareBuy — Marketplace Price Scraper
Fetches prices from Tokopedia, Shopee, and Lazada.
Uses httpx + BeautifulSoup with graceful fallback to cached prices.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.models import MarketplacePrice, PriceResponse

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TIMEOUT = httpx.Timeout(10.0, connect=5.0)

# Jakarta timezone
WIB = timezone(timedelta(hours=7))


# ──────────────────────────────────────────────
# Realistic Fallback Prices (Indonesian market)
# ──────────────────────────────────────────────
FALLBACK_PRICES: dict[str, list[MarketplacePrice]] = {
    "sm-001": [
        MarketplacePrice(marketplace="Tokopedia", price=19499000, url="https://www.tokopedia.com/search?q=samsung+galaxy+s24+ultra", seller="Samsung Official Store", available=True, target_configuration="Acuan Simulasi: 12 GB RAM / 256 GB UFS 4.0"),
        MarketplacePrice(marketplace="Shopee", price=19299000, url="https://shopee.co.id/search?keyword=samsung+galaxy+s24+ultra", seller="Samsung Official Shop", available=True, target_configuration="Acuan Simulasi: 12 GB RAM / 256 GB UFS 4.0"),
        MarketplacePrice(marketplace="Lazada", price=19599000, url="https://www.lazada.co.id/catalog/?q=samsung+galaxy+s24+ultra", seller="Samsung Flagship", available=True, target_configuration="Acuan Simulasi: 12 GB RAM / 256 GB UFS 4.0"),
    ],
    "sm-002": [
        MarketplacePrice(marketplace="Tokopedia", price=21999000, url="https://www.tokopedia.com/search?q=iphone+15+pro+max", seller="iBox Official", available=True, target_configuration="Acuan Simulasi: 8 GB RAM / 256 GB Penyimpanan Flash Internal"),
        MarketplacePrice(marketplace="Shopee", price=22199000, url="https://shopee.co.id/search?keyword=iphone+15+pro+max", seller="iBox Official Shop", available=True, target_configuration="Acuan Simulasi: 8 GB RAM / 256 GB Penyimpanan Flash Internal"),
        MarketplacePrice(marketplace="Lazada", price=22099000, url="https://www.lazada.co.id/catalog/?q=iphone+15+pro+max", seller="Apple Official", available=True, target_configuration="Acuan Simulasi: 8 GB RAM / 256 GB Penyimpanan Flash Internal"),
    ],
    "sm-003": [
        MarketplacePrice(marketplace="Tokopedia", price=13999000, url="https://www.tokopedia.com/search?q=google+pixel+8+pro", seller="Marketplace Seller / Impor", available=True, target_configuration="Acuan Simulasi: 12 GB RAM / 128 GB UFS 3.1"),
        MarketplacePrice(marketplace="Shopee", price=14299000, url="https://shopee.co.id/search?keyword=google+pixel+8+pro", seller="Marketplace Seller / Impor", available=True, target_configuration="Acuan Simulasi: 12 GB RAM / 128 GB UFS 3.1"),
        MarketplacePrice(marketplace="Lazada", price=14499000, url="https://www.lazada.co.id/catalog/?q=google+pixel+8+pro", seller="Marketplace Seller / Impor", available=True, target_configuration="Acuan Simulasi: 12 GB RAM / 128 GB UFS 3.1"),
    ],
    "sm-004": [
        MarketplacePrice(marketplace="Tokopedia", price=14499000, url="https://www.tokopedia.com/search?q=xiaomi+14+ultra", seller="Marketplace Seller / Impor", available=True, target_configuration="Acuan Simulasi: 16 GB LPDDR5X / 512 GB UFS 4.0"),
        MarketplacePrice(marketplace="Shopee", price=14699000, url="https://shopee.co.id/search?keyword=xiaomi+14+ultra", seller="Marketplace Seller / Impor", available=True, target_configuration="Acuan Simulasi: 16 GB LPDDR5X / 512 GB UFS 4.0"),
        MarketplacePrice(marketplace="Lazada", price=14399000, url="https://www.lazada.co.id/catalog/?q=xiaomi+14+ultra", seller="Marketplace Seller / Impor", available=True, target_configuration="Acuan Simulasi: 16 GB LPDDR5X / 512 GB UFS 4.0"),
    ],
    "sm-005": [
        MarketplacePrice(marketplace="Tokopedia", price=3849000, url="https://www.tokopedia.com/search?q=poco+x6+pro", seller="POCO Official", available=True, target_configuration="Acuan Simulasi: 12 GB LPDDR5X / 512 GB UFS 4.0"),
        MarketplacePrice(marketplace="Shopee", price=3799000, url="https://shopee.co.id/search?keyword=poco+x6+pro", seller="POCO Official Shop", available=True, target_configuration="Acuan Simulasi: 12 GB LPDDR5X / 512 GB UFS 4.0"),
        MarketplacePrice(marketplace="Lazada", price=3899000, url="https://www.lazada.co.id/catalog/?q=poco+x6+pro", seller="POCO Store", available=True, target_configuration="Acuan Simulasi: 12 GB LPDDR5X / 512 GB UFS 4.0"),
    ],
    "sm-006": [
        MarketplacePrice(marketplace="Tokopedia", price=5299000, url="https://www.tokopedia.com/search?q=samsung+galaxy+a55", seller="Samsung Official", available=True, target_configuration="Acuan Simulasi: 8 GB RAM / 256 GB UFS 3.1"),
        MarketplacePrice(marketplace="Shopee", price=5199000, url="https://shopee.co.id/search?keyword=samsung+galaxy+a55", seller="Samsung Official Shop", available=True, target_configuration="Acuan Simulasi: 8 GB RAM / 256 GB UFS 3.1"),
        MarketplacePrice(marketplace="Lazada", price=5399000, url="https://www.lazada.co.id/catalog/?q=samsung+galaxy+a55", seller="Samsung Store", available=True, target_configuration="Acuan Simulasi: 8 GB RAM / 256 GB UFS 3.1"),
    ],
    "lp-001": [
        MarketplacePrice(marketplace="Tokopedia", price=17999000, url="https://www.tokopedia.com/search?q=macbook+air+m3", seller="iBox Official", available=True, target_configuration="Acuan Simulasi: 8 GB Unified Memory / 256 GB SSD"),
        MarketplacePrice(marketplace="Shopee", price=18199000, url="https://shopee.co.id/search?keyword=macbook+air+m3", seller="iBox Official Shop", available=True, target_configuration="Acuan Simulasi: 8 GB Unified Memory / 256 GB SSD"),
        MarketplacePrice(marketplace="Lazada", price=18299000, url="https://www.lazada.co.id/catalog/?q=macbook+air+m3", seller="Apple Official", available=True, target_configuration="Acuan Simulasi: 8 GB Unified Memory / 256 GB SSD"),
    ],
    "lp-002": [
        MarketplacePrice(marketplace="Tokopedia", price=28499000, url="https://www.tokopedia.com/search?q=rog+zephyrus+g14", seller="ASUS Official", available=True, target_configuration="Acuan Simulasi: Ryzen 9 8945HS / RTX 4060 / 16 GB LPDDR5X / 1 TB SSD PCIe 4.0"),
        MarketplacePrice(marketplace="Shopee", price=28799000, url="https://shopee.co.id/search?keyword=rog+zephyrus+g14", seller="ASUS ROG Official", available=True, target_configuration="Acuan Simulasi: Ryzen 9 8945HS / RTX 4060 / 16 GB LPDDR5X / 1 TB SSD PCIe 4.0"),
        MarketplacePrice(marketplace="Lazada", price=28599000, url="https://www.lazada.co.id/catalog/?q=rog+zephyrus+g14", seller="ASUS Store", available=True, target_configuration="Acuan Simulasi: Ryzen 9 8945HS / RTX 4060 / 16 GB LPDDR5X / 1 TB SSD PCIe 4.0"),
    ],
    "lp-003": [
        MarketplacePrice(marketplace="Tokopedia", price=24499000, url="https://www.tokopedia.com/search?q=thinkpad+x1+carbon", seller="Lenovo Official", available=True, target_configuration="Acuan Simulasi: Intel Core i7-1365U / 16 GB LPDDR5 / 512 GB PCIe Gen4 SSD"),
        MarketplacePrice(marketplace="Shopee", price=24799000, url="https://shopee.co.id/search?keyword=thinkpad+x1+carbon", seller="Lenovo Official Shop", available=True, target_configuration="Acuan Simulasi: Intel Core i7-1365U / 16 GB LPDDR5 / 512 GB PCIe Gen4 SSD"),
        MarketplacePrice(marketplace="Lazada", price=24699000, url="https://www.lazada.co.id/catalog/?q=thinkpad+x1+carbon", seller="Lenovo Store", available=True, target_configuration="Acuan Simulasi: Intel Core i7-1365U / 16 GB LPDDR5 / 512 GB PCIe Gen4 SSD"),
    ],
    "lp-004": [
        MarketplacePrice(marketplace="Tokopedia", price=8299000, url="https://www.tokopedia.com/search?q=acer+aspire+5", seller="Acer Official", available=True, target_configuration="Acuan Simulasi: Intel Core i5-1335U / 8 GB LPDDR5 / 512 GB SSD PCIe Gen4"),
        MarketplacePrice(marketplace="Shopee", price=8199000, url="https://shopee.co.id/search?keyword=acer+aspire+5", seller="Acer Official Shop", available=True, target_configuration="Acuan Simulasi: Intel Core i5-1335U / 8 GB LPDDR5 / 512 GB SSD PCIe Gen4"),
        MarketplacePrice(marketplace="Lazada", price=8399000, url="https://www.lazada.co.id/catalog/?q=acer+aspire+5", seller="Acer Store", available=True, target_configuration="Acuan Simulasi: Intel Core i5-1335U / 8 GB LPDDR5 / 512 GB SSD PCIe Gen4"),
    ],
    "lp-005": [
        MarketplacePrice(marketplace="Tokopedia", price=13699000, url="https://www.tokopedia.com/search?q=lenovo+loq+15", seller="Lenovo Official", available=True, target_configuration="Acuan Simulasi: Intel Core i5-13450HX / RTX 4050 / 16 GB DDR5 / 512 GB PCIe 4.0 SSD"),
        MarketplacePrice(marketplace="Shopee", price=13599000, url="https://shopee.co.id/search?keyword=lenovo+loq+15", seller="Lenovo Gaming Official", available=True, target_configuration="Acuan Simulasi: Intel Core i5-13450HX / RTX 4050 / 16 GB DDR5 / 512 GB PCIe 4.0 SSD"),
        MarketplacePrice(marketplace="Lazada", price=13799000, url="https://www.lazada.co.id/catalog/?q=lenovo+loq+15", seller="Lenovo Store", available=True, target_configuration="Acuan Simulasi: Intel Core i5-13450HX / RTX 4050 / 16 GB DDR5 / 512 GB PCIe 4.0 SSD"),
    ],
    "tb-001": [
        MarketplacePrice(marketplace="Tokopedia", price=10799000, url="https://www.tokopedia.com/search?q=ipad+air+m2", seller="iBox Official", available=True, target_configuration="Acuan Simulasi: Apple M2 / 8 GB RAM / 128 GB Penyimpanan Flash"),
        MarketplacePrice(marketplace="Shopee", price=10699000, url="https://shopee.co.id/search?keyword=ipad+air+m2", seller="iBox Official Shop", available=True, target_configuration="Acuan Simulasi: Apple M2 / 8 GB RAM / 128 GB Penyimpanan Flash"),
        MarketplacePrice(marketplace="Lazada", price=10899000, url="https://www.lazada.co.id/catalog/?q=ipad+air+m2", seller="Apple Official", available=True, target_configuration="Acuan Simulasi: Apple M2 / 8 GB RAM / 128 GB Penyimpanan Flash"),
    ],
    "tb-002": [
        MarketplacePrice(marketplace="Tokopedia", price=6299000, url="https://www.tokopedia.com/search?q=galaxy+tab+s9+fe", seller="Samsung Official", available=True, target_configuration="Acuan Simulasi: Exynos 1380 / 6 GB RAM / 128 GB UFS"),
        MarketplacePrice(marketplace="Shopee", price=6199000, url="https://shopee.co.id/search?keyword=galaxy+tab+s9+fe", seller="Samsung Official Shop", available=True, target_configuration="Acuan Simulasi: Exynos 1380 / 6 GB RAM / 128 GB UFS"),
        MarketplacePrice(marketplace="Lazada", price=6399000, url="https://www.lazada.co.id/catalog/?q=galaxy+tab+s9+fe", seller="Samsung Store", available=True, target_configuration="Acuan Simulasi: Exynos 1380 / 6 GB RAM / 128 GB UFS"),
    ],
    "tw-001": [
        MarketplacePrice(marketplace="Tokopedia", price=3699000, url="https://www.tokopedia.com/search?q=airpods+pro+2", seller="iBox Official", available=True, target_configuration="Acuan Simulasi: Model Tunggal Standar (MagSafe Case USB-C)"),
        MarketplacePrice(marketplace="Shopee", price=3649000, url="https://shopee.co.id/search?keyword=airpods+pro+2", seller="iBox Official Shop", available=True, target_configuration="Acuan Simulasi: Model Tunggal Standar (MagSafe Case USB-C)"),
        MarketplacePrice(marketplace="Lazada", price=3749000, url="https://www.lazada.co.id/catalog/?q=airpods+pro+2", seller="Apple Official", available=True, target_configuration="Acuan Simulasi: Model Tunggal Standar (MagSafe Case USB-C)"),
    ],
    "tw-002": [
        MarketplacePrice(marketplace="Tokopedia", price=4199000, url="https://www.tokopedia.com/search?q=sony+wf-1000xm5", seller="Sony Official", available=True, target_configuration="Acuan Simulasi: Model Tunggal Standar (Dual Dynamic Driver X, ANC)"),
        MarketplacePrice(marketplace="Shopee", price=4099000, url="https://shopee.co.id/search?keyword=sony+wf-1000xm5", seller="Sony Official Shop", available=True, target_configuration="Acuan Simulasi: Model Tunggal Standar (Dual Dynamic Driver X, ANC)"),
        MarketplacePrice(marketplace="Lazada", price=4249000, url="https://www.lazada.co.id/catalog/?q=sony+wf-1000xm5", seller="Sony Store", available=True, target_configuration="Acuan Simulasi: Model Tunggal Standar (Dual Dynamic Driver X, ANC)"),
    ],
    "tw-003": [
        MarketplacePrice(marketplace="Tokopedia", price=3199000, url="https://www.tokopedia.com/search?q=galaxy+buds3+pro", seller="Samsung Official", available=True, target_configuration="Acuan Simulasi: Model Tunggal Standar (Dual Driver 2-way, Blade Light, ANC)"),
        MarketplacePrice(marketplace="Shopee", price=3149000, url="https://shopee.co.id/search?keyword=galaxy+buds3+pro", seller="Samsung Official Shop", available=True, target_configuration="Acuan Simulasi: Model Tunggal Standar (Dual Driver 2-way, Blade Light, ANC)"),
        MarketplacePrice(marketplace="Lazada", price=3249000, url="https://www.lazada.co.id/catalog/?q=galaxy+buds3+pro", seller="Samsung Store", available=True, target_configuration="Acuan Simulasi: Model Tunggal Standar (Dual Driver 2-way, Blade Light, ANC)"),
    ],
    "tw-004": [
        MarketplacePrice(marketplace="Tokopedia", price=329000, url="https://www.tokopedia.com/search?q=qcy+melobuds+anc", seller="QCY Official", available=True, target_configuration="Acuan Simulasi: Model Tunggal Standar (10mm Driver, 40 dB Hybrid ANC, Bluetooth 5.2)"),
        MarketplacePrice(marketplace="Shopee", price=319000, url="https://shopee.co.id/search?keyword=qcy+melobuds+anc", seller="QCY Official Shop", available=True, target_configuration="Acuan Simulasi: Model Tunggal Standar (10mm Driver, 40 dB Hybrid ANC, Bluetooth 5.2)"),
        MarketplacePrice(marketplace="Lazada", price=339000, url="https://www.lazada.co.id/catalog/?q=qcy+melobuds+anc", seller="QCY Store", available=True, target_configuration="Acuan Simulasi: Model Tunggal Standar (10mm Driver, 40 dB Hybrid ANC, Bluetooth 5.2)"),
    ],
    "sw-001": [
        MarketplacePrice(marketplace="Tokopedia", price=13799000, url="https://www.tokopedia.com/search?q=apple+watch+ultra+2", seller="iBox Official", available=True, target_configuration="Acuan Simulasi: Kasus Titanium 49mm GPS + Cellular"),
        MarketplacePrice(marketplace="Shopee", price=13699000, url="https://shopee.co.id/search?keyword=apple+watch+ultra+2", seller="iBox Official Shop", available=True, target_configuration="Acuan Simulasi: Kasus Titanium 49mm GPS + Cellular"),
        MarketplacePrice(marketplace="Lazada", price=13899000, url="https://www.lazada.co.id/catalog/?q=apple+watch+ultra+2", seller="Apple Official", available=True, target_configuration="Acuan Simulasi: Kasus Titanium 49mm GPS + Cellular"),
    ],
    "sw-002": [
        MarketplacePrice(marketplace="Tokopedia", price=4399000, url="https://www.tokopedia.com/search?q=galaxy+watch+7", seller="Samsung Official", available=True, target_configuration="Acuan Simulasi: Kasus Aluminium 40mm Bluetooth"),
        MarketplacePrice(marketplace="Shopee", price=4299000, url="https://shopee.co.id/search?keyword=galaxy+watch+7", seller="Samsung Official Shop", available=True, target_configuration="Acuan Simulasi: Kasus Aluminium 40mm Bluetooth"),
        MarketplacePrice(marketplace="Lazada", price=4449000, url="https://www.lazada.co.id/catalog/?q=galaxy+watch+7", seller="Samsung Store", available=True, target_configuration="Acuan Simulasi: Kasus Aluminium 40mm Bluetooth"),
    ],
    "sw-003": [
        MarketplacePrice(marketplace="Tokopedia", price=2899000, url="https://www.tokopedia.com/search?q=amazfit+gtr+4", seller="Amazfit Official", available=True, target_configuration="Acuan Simulasi: Kasus Aluminium 46mm AMOLED GPS"),
        MarketplacePrice(marketplace="Shopee", price=2799000, url="https://shopee.co.id/search?keyword=amazfit+gtr+4", seller="Amazfit Official Shop", available=True, target_configuration="Acuan Simulasi: Kasus Aluminium 46mm AMOLED GPS"),
        MarketplacePrice(marketplace="Lazada", price=2949000, url="https://www.lazada.co.id/catalog/?q=amazfit+gtr+4", seller="Amazfit Store", available=True, target_configuration="Acuan Simulasi: Kasus Aluminium 46mm AMOLED GPS"),
    ],
}

OFFICIAL_MARKETPLACE_DOMAINS = ("tokopedia.com", "shopee.co.id", "lazada.co.id")


def is_valid_marketplace_url(url: str) -> bool:
    """Return True only for http/https URLs on an official marketplace domain or its subdomain."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url.strip())
        hostname = parsed.hostname
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https") or not hostname:
        return False
    hostname = hostname.lower().rstrip(".")
    return any(
        hostname == domain or hostname.endswith("." + domain)
        for domain in OFFICIAL_MARKETPLACE_DOMAINS
    )


# ──────────────────────────────────────────────
# Price Parsing & Validation Helper
# ──────────────────────────────────────────────
def parse_marketplace_price(
    raw_text: str,
    listing_title: str = "",
    expected_product_name: str = "",
    title: str = ""
) -> Optional[int]:
    """
    Parse and validate marketplace price string.
    - Validates product relevance (rejects non-gadget accessories like cases, straps, tempered glass).
    - Rejects installment / cicilan formats (/bln, /bulan, /mo, per bulan, cicilan, installment).
    - Normalizes Rupiah format (removes decimal sen, dot separators, Rp/IDR tokens).
    - Handles price ranges (extracts lower bound).
    - Bounds checking: returns None if outside realistic range (Rp 50.000 - Rp 150.000.000).
    """
    if not raw_text or not isinstance(raw_text, str):
        return None

    actual_title = listing_title or title

    # 1. Product relevance check
    if actual_title:
        title_lower = actual_title.lower()
        accessory_keywords = [
            "casing", "case ", " case", "silikon", "silicone",
            "tempered glass", "anti gores", "antigores", "hydrogel",
            "strap ", "strap", "tali jam", "charger only", "kabel charger", "kabel only", "adapter only"
        ]
        expected_lower = expected_product_name.lower() if expected_product_name else ""
        if not any(k in expected_lower for k in ["case", "strap"]):
            if any(k in title_lower for k in accessory_keywords):
                return None

    # 2. Reject installment / cicilan patterns
    text_lower = raw_text.lower()
    installment_patterns = ["/bln", "/bulan", "/mo", "per bulan", "cicilan", "installment", "/ bln", "/ bulan"]
    if any(pat in text_lower for pat in installment_patterns):
        return None

    # 3. Handle price range (e.g. "Rp 18.000.000 - Rp 20.000.000")
    if " - " in raw_text or " – " in raw_text or " — " in raw_text:
        import re
        parts = re.split(r'\s*[-–—]\s*', raw_text)
        if parts:
            raw_text = parts[0]

    # 4. Normalize Rupiah string
    import re
    # Remove Rp or IDR prefix case-insensitively
    cleaned = re.sub(r'(?i)(?:rp|idr)\.?\s*', '', raw_text).strip()
    # Remove decimal sen suffix like ,00 or .00 at the end
    cleaned = re.sub(r'[,.]\d{2}$', '', cleaned)
    # Remove dots, commas, and whitespace
    digits_only = re.sub(r'[\.,\s]', '', cleaned)

    if not digits_only.isdigit():
        return None

    price = int(digits_only)

    # 5. Sanity bounds check
    if price < 50_000 or price > 150_000_000:
        return None

    return price



# ──────────────────────────────────────────────
# Scraping Helpers
# ──────────────────────────────────────────────
async def _scrape_tokopedia(product_name: str) -> Optional[MarketplacePrice]:
    """Attempt to scrape Tokopedia search results with validation."""
    try:
        search_url = f"https://www.tokopedia.com/search?q={product_name.replace(' ', '+')}"
        async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(search_url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                price_el = soup.select_one('[data-testid="spnSRPProdPrice"]')
                title_el = soup.select_one('[data-testid="spnSRPProdName"]')
                listing_title = title_el.text.strip() if title_el else ""
                if price_el:
                    price = parse_marketplace_price(
                        price_el.text,
                        listing_title=listing_title,
                        expected_product_name=product_name
                    )
                    if price:
                        return MarketplacePrice(
                            marketplace="Tokopedia",
                            price=price,
                            url=search_url,
                            seller="Tokopedia Seller",
                            available=True,
                            source="scraped",
                            captured_at=datetime.now(timezone.utc).isoformat()
                        )
    except Exception as e:
        logger.warning(f"Tokopedia scraping failed: {e}")
    return None


async def _scrape_shopee(product_name: str) -> Optional[MarketplacePrice]:
    """Attempt to scrape Shopee search results with validation."""
    try:
        search_url = f"https://shopee.co.id/search?keyword={product_name.replace(' ', '+')}"
        async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(search_url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                price_el = soup.select_one(".shopee-price")
                title_el = soup.select_one(".shopee-search-item-result__item-name")
                listing_title = title_el.text.strip() if title_el else ""
                if price_el:
                    price = parse_marketplace_price(
                        price_el.text,
                        listing_title=listing_title,
                        expected_product_name=product_name
                    )
                    if price:
                        return MarketplacePrice(
                            marketplace="Shopee",
                            price=price,
                            url=search_url,
                            seller="Shopee Seller",
                            available=True,
                            source="scraped",
                            captured_at=datetime.now(timezone.utc).isoformat()
                        )
    except Exception as e:
        logger.warning(f"Shopee scraping failed: {e}")
    return None


async def _scrape_lazada(product_name: str) -> Optional[MarketplacePrice]:
    """Attempt to scrape Lazada search results with validation."""
    try:
        search_url = f"https://www.lazada.co.id/catalog/?q={product_name.replace(' ', '+')}"
        async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(search_url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                price_el = soup.select_one(".price--NVB62")
                title_el = soup.select_one(".title--wFj93")
                listing_title = title_el.text.strip() if title_el else ""
                if price_el:
                    price = parse_marketplace_price(
                        price_el.text,
                        listing_title=listing_title,
                        expected_product_name=product_name
                    )
                    if price:
                        return MarketplacePrice(
                            marketplace="Lazada",
                            price=price,
                            url=search_url,
                            seller="Lazada Seller",
                            available=True,
                            source="scraped",
                            captured_at=datetime.now(timezone.utc).isoformat()
                        )
    except Exception as e:
        logger.warning(f"Lazada scraping failed: {e}")
    return None


# ──────────────────────────────────────────────
# Main Scraper Function
# ──────────────────────────────────────────────
async def get_live_prices(product_id: str, product_name: str) -> PriceResponse:
    """
    Attempt live scraping from all 3 marketplaces.
    Falls back to cached/realistic prices if scraping fails.
    Deterministic fallback — NO random offsets.
    """
    now = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S WIB")
    utc_now_iso = datetime.now(timezone.utc).isoformat()

    # Try scraping in parallel
    results = await asyncio.gather(
        _scrape_tokopedia(product_name),
        _scrape_shopee(product_name),
        _scrape_lazada(product_name),
        return_exceptions=True
    )

    prices: list[MarketplacePrice] = []
    scraped_marketplaces = set()

    for result in results:
        if isinstance(result, MarketplacePrice):
            prices.append(result)
            scraped_marketplaces.add(result.marketplace)

    # Fall back to cached prices for any marketplace that failed
    fallback = FALLBACK_PRICES.get(product_id, [])
    for fb in fallback:
        if fb.marketplace not in scraped_marketplaces:
            # Deterministic reference price from official/verified catalog
            prices.append(MarketplacePrice(
                marketplace=fb.marketplace,
                price=fb.price,
                url=fb.url,
                seller=fb.seller,
                available=fb.available,
                source="fallback",
                captured_at=None,  # Explicitly null on API response for fallback
                target_configuration=fb.target_configuration
            ))

    # Sort by price ascending (best deal first)
    prices.sort(key=lambda p: p.price)

    # Persist snapshot to database if repository is available
    try:
        from app.repositories.price_repo import save_price_snapshot
        for p in prices:
            save_price_snapshot(
                product_id=product_id,
                marketplace_code=p.marketplace.lower(),
                price=p.price,
                seller=p.seller,
                url=p.url,
                available=p.available,
                source=p.source,
                captured_at=p.captured_at or utc_now_iso
            )
    except Exception as e:
        logger.debug(f"Snapshot persistence skipped: {e}")

    # Transparent last_updated label
    last_updated_label = now if len(scraped_marketplaces) > 0 else "Data acuan fallback (Belum diverifikasi live)"

    return PriceResponse(
        product_id=product_id,
        product_name=product_name,
        prices=prices,
        last_updated=last_updated_label
    )
