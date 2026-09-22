from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1. Health check
res = client.get('/health')
assert res.status_code == 200, f'Health failed: {res.status_code}'
print('[OK] Health check passed')

# 2. Catalog endpoint
res = client.get('/api/products')
assert res.status_code == 200, f'Catalog failed: {res.status_code}'
data = res.json()
assert data['total'] >= 15, f"Products total too low: {data['total']}"
print(f"[OK] Catalog endpoint passed: {data['total']} products loaded")

# 3. Scoring endpoint
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
top_item = score_data['results'][0]
print(f"[OK] Scoring endpoint passed! Top pick: {top_item['product']['name']} (Score: {top_item['total_score']})")

# 4. Compare endpoint
compare_payload = {'product_ids': ['sm-001', 'sm-002']}
res = client.post('/api/compare', json=compare_payload)
assert res.status_code == 200, f'Compare failed: {res.status_code}'
compare_data = res.json()
assert len(compare_data['products']) == 2, 'Compare products mismatch'
print(f"[OK] Compare endpoint passed: {len(compare_data['highlights'])} spec comparison highlights generated")

# 5. Prices endpoint (Live marketplace fallback test)
res = client.get('/api/prices/sm-001')
assert res.status_code == 200, f'Prices failed: {res.status_code}'
price_data = res.json()
assert len(price_data['prices']) == 3, 'Marketplace prices count mismatch'
print(f"[OK] Live Prices endpoint passed! Marketplaces: {[p['marketplace'] for p in price_data['prices']]}")

print('\n=== ALL 5 FASTAPI CORE ENDPOINTS VERIFIED AND WORKING! ===')
