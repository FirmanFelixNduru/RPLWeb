import asyncio
from unittest.mock import patch

from fastapi.testclient import TestClient
import httpx
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError

from app import scraper
from app.db import SessionLocal, engine, is_db_connected
from app.entities import MarketplacePrice, Product, ProductSpecs
from app.models import MarketplacePrice as MarketplacePriceModel
from app.main import app

client = TestClient(app)

# 1. Service and health checks
res = client.get('/')
assert res.status_code == 200 and res.json()['status'] == 'healthy', 'Root endpoint failed'
print('[OK] Root endpoint passed')

res = client.get('/health')
assert res.status_code == 200, f'Health failed: {res.status_code}'
print('[OK] Health check passed')

# 2. Catalog, search, query validation, and product detail
res = client.get('/api/products')
assert res.status_code == 200, f'Catalog failed: {res.status_code}'
data = res.json()
assert data['total'] >= 15, f"Products total too low: {data['total']}"
print(f"[OK] Catalog endpoint passed: {data['total']} products loaded")

page_res = client.get('/api/products?page=1&per_page=5')
assert page_res.status_code == 200 and len(page_res.json()['products']) == 5
assert page_res.json()['total'] == data['total']
assert client.get('/api/products?search=Samsung').json()['total'] > 0
assert client.get('/api/products?category=laptop&sort_by=price_asc').status_code == 200
assert client.get('/api/products?tags=flagship').json()['total'] > 0
assert client.get('/api/products?category=unknown').status_code == 422
assert client.get('/api/products?sort_by=unknown').status_code == 422

detail_res = client.get('/api/products/sm-001')
assert detail_res.status_code == 200 and detail_res.json()['id'] == 'sm-001'
assert client.get('/api/products/not-a-product').status_code == 404
print('[OK] Catalog query, pagination, and detail checks passed')

# 3. Scoring endpoint and input validation
payload = {
    'category': 'smartphone',
    'budget_min': 3000000,
    'budget_max': 15000000,
    'scenarios': ['gaming', 'photography'],
    'priorities': {'performance': 5, 'camera': 4, 'battery': 4}
}
res = client.post('/api/score', json=payload)
assert res.status_code == 200, f'Scoring failed: {res.status_code}'
score_data = res.json()
assert len(score_data['results']) > 0, 'No scored products returned'
assert len(score_data['results'][0]['score_breakdown']) == 8
assert score_data['results'][0]['why_this_product']
top_item = score_data['results'][0]
print(f"[OK] Scoring endpoint passed! Top pick: {top_item['product']['name']} (Score: {top_item['total_score']})")
assert client.post('/api/score', json={**payload, 'budget_min': 20000000}).status_code == 422
assert client.post('/api/score', json={**payload, 'priorities': {'performance': 6}}).status_code == 422

# 4. Comparison endpoint and limits
compare_payload = {'product_ids': ['sm-001', 'sm-002']}
res = client.post('/api/compare', json=compare_payload)
assert res.status_code == 200, f'Compare failed: {res.status_code}'
compare_data = res.json()
assert len(compare_data['products']) == 2, 'Compare products mismatch'
print(f"[OK] Compare endpoint passed: {len(compare_data['highlights'])} spec comparison highlights generated")
for product_ids in (
    ['sm-001', 'sm-002', 'sm-003'],
    ['sm-001', 'sm-002', 'sm-003', 'sm-004'],
):
    result = client.post('/api/compare', json={'product_ids': product_ids})
    assert result.status_code == 200 and len(result.json()['products']) == len(product_ids)
assert client.post('/api/compare', json={'product_ids': ['sm-001'] * 5}).status_code == 422
assert client.post('/api/compare', json={'product_ids': ['sm-001', 'missing']}).status_code == 404

# 5. Prices endpoint and source contract
db_product = None
snapshot_count = None
if is_db_connected():
    session = SessionLocal()
    db_product = session.query(Product).filter(Product.id == 'sm-001').first()
    snapshot_count = session.query(MarketplacePrice).filter(
        MarketplacePrice.product_id == 'sm-001'
    ).count()
    session.close()
    assert db_product is not None
    original_msrp = db_product.price

res = client.get('/api/prices/sm-001')
assert res.status_code == 200, f'Prices failed: {res.status_code}'
price_data = res.json()
assert len(price_data['prices']) == 3, 'Marketplace prices count mismatch'
for p in price_data['prices']:
    assert 'source' in p, f"Price missing 'source' field: {p}"
    assert p['source'] in ('scraped', 'fallback'), f"Invalid source: {p['source']}"
print(f"[OK] Live Prices endpoint passed! Marketplaces: {[p['marketplace'] for p in price_data['prices']]}")

async def scraper_failure(product_name):
    raise RuntimeError('Simulated marketplace failure')


original_scrapers = (
    scraper._scrape_tokopedia,
    scraper._scrape_shopee,
    scraper._scrape_lazada,
)
scraper._scrape_tokopedia = scraper_failure
scraper._scrape_shopee = scraper_failure
scraper._scrape_lazada = scraper_failure
try:
    fallback_data = asyncio.run(scraper.get_live_prices('sm-001', 'Samsung Galaxy S24 Ultra'))
    assert len(fallback_data.prices) == 3
    assert all(price.source == 'fallback' for price in fallback_data.prices)
finally:
    (
        scraper._scrape_tokopedia,
        scraper._scrape_shopee,
        scraper._scrape_lazada,
    ) = original_scrapers
print('[OK] Marketplace failure returns explicitly marked fallback prices')


async def scraped_tokopedia(product_name):
    return MarketplacePriceModel(
        marketplace='Tokopedia',
        price=100,
        url='https://tokopedia.com/example',
        source='scraped',
        captured_at='2026-09-30T00:00:00+00:00',
    )


async def scraper_timeout(product_name):
    raise httpx.TimeoutException('Simulated marketplace timeout')


async def scraper_network_failure(product_name):
    raise httpx.ConnectError('Simulated marketplace network failure')


scraper._scrape_tokopedia = scraped_tokopedia
scraper._scrape_shopee = scraper_timeout
scraper._scrape_lazada = scraper_network_failure
try:
    partial_data = asyncio.run(scraper.get_live_prices('sm-001', 'Samsung Galaxy S24 Ultra'))
    sources_by_marketplace = {price.marketplace: price.source.value for price in partial_data.prices}
    assert sources_by_marketplace['Tokopedia'] == 'scraped'
    assert sources_by_marketplace['Shopee'] == 'fallback'
    assert sources_by_marketplace['Lazada'] == 'fallback'
finally:
    (
        scraper._scrape_tokopedia,
        scraper._scrape_shopee,
        scraper._scrape_lazada,
    ) = original_scrapers
print('[OK] Timeout and network failure preserve other marketplace results')


class InvalidPriceResponse:
    status_code = 200
    text = '<span data-testid="spnSRPProdPrice">Rp invalid</span>'


class InvalidPriceClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return False

    async def get(self, url):
        return InvalidPriceResponse()


with patch.object(scraper.httpx, 'AsyncClient', InvalidPriceClient):
    invalid_price = asyncio.run(scraper._scrape_tokopedia('Test Product'))
assert invalid_price is None
print('[OK] Invalid marketplace price markup safely falls back')

# 6. Metadata endpoints: brands, tags, categories
res = client.get('/api/brands')
assert res.status_code == 200, f'Brands failed: {res.status_code}'
assert len(res.json()['brands']) > 0, 'No brands returned'
print(f"[OK] Brands endpoint passed: {len(res.json()['brands'])} unique brands")

res = client.get('/api/tags')
assert res.status_code == 200, f'Tags failed: {res.status_code}'
assert len(res.json()['tags']) > 0, 'No tags returned'
print(f"[OK] Tags endpoint passed: {len(res.json()['tags'])} unique tags")

res = client.get('/api/categories')
assert res.status_code == 200, f'Categories failed: {res.status_code}'
assert len(res.json()['categories']) == 5, 'Expected 5 categories'
print(f"[OK] Categories endpoint passed: {[c['value'] for c in res.json()['categories']]}")

# 7. Distinct product validation on comparison
dup_res = client.post('/api/compare', json={'product_ids': ['sm-001', 'sm-001']})
assert dup_res.status_code in (400, 422), f'Expected error for duplicate IDs, got {dup_res.status_code}'
print('[OK] Comparison validation correctly rejects duplicate product IDs')

# 8. Database and Entity schema verification
from app.entities import (
    Brand, Product, ProductSpecs, ReviewSentiment,
    WarrantyInfo, Tag, ProductTag, Marketplace,
    MarketplaceLink, MarketplacePrice
)
assert Product.__tablename__ == 'products'
assert Brand.__tablename__ == 'brands'
print('[OK] SQLAlchemy 2.x entities verified successfully')
assert 'JSONB' in str(ProductSpecs.__table__.c.specifications.type.compile(dialect=postgresql.dialect()))

if is_db_connected():
    session = SessionLocal()
    assert session.query(Product).count() == 20
    assert session.query(MarketplacePrice).filter(
        MarketplacePrice.product_id == 'sm-001'
    ).count() >= snapshot_count + len(price_data['prices'])
    assert session.query(Product.price).filter(Product.id == 'sm-001').scalar() == original_msrp
    session.close()

    with engine.connect() as connection:
        if connection.dialect.name == 'sqlite':
            connection.exec_driver_sql('PRAGMA foreign_keys=ON')
            connection.commit()
        invalid_statements = (
            "INSERT INTO brands (name) VALUES ('')",
            "INSERT INTO marketplace_prices "
            "(product_id, marketplace_id, price, url, source, captured_at) "
            "VALUES ('sm-001', 1, 100, 'https://example.com', 'invalid', CURRENT_TIMESTAMP)",
            "INSERT INTO marketplace_prices "
            "(product_id, marketplace_id, price, url, source, captured_at) "
            "VALUES ('sm-001', 1, 0, 'https://example.com', 'fallback', CURRENT_TIMESTAMP)",
            "INSERT INTO marketplace_prices "
            "(product_id, marketplace_id, price, url, source, captured_at) "
            "VALUES ('missing', 1, 100, 'https://example.com', 'fallback', CURRENT_TIMESTAMP)",
        )
        for statement in invalid_statements:
            try:
                with connection.begin():
                    connection.execute(text(statement))
            except IntegrityError:
                pass
            else:
                raise AssertionError(f'Database constraint did not reject: {statement}')
    print('[OK] DB persistence, MSRP stability, source/price/FK constraints verified')

assert MarketplacePriceModel(url='https://example.com', marketplace='Example', price=1)
try:
    MarketplacePriceModel(url='not-a-url', marketplace='Example', price=1)
except Exception:
    pass
else:
    raise AssertionError('Marketplace price accepted an invalid URL')

print('\n=== API CORE ENDPOINTS AND AVAILABLE DATABASE CHECKS PASSED ===')
