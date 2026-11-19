const assert = require('node:assert/strict');
const { test } = require('node:test');
const React = require('react');
const load = require('./helpers/load-source.cjs');
const dimensions = ['performance', 'camera', 'battery', 'display', 'value'];
const all = value => Object.fromEntries(dimensions.map(d => [`score_${d}`, value]));
const { getCatalogScore } = load('lib/catalogScore.js');

// 20 score contracts: zero, null/missing defaults, each dimension and rounding.
const scoreCases = [
  ['zero is a valid score, not a missing value', all(0), 0],
  ['missing dimensions use neutral defaults', {}, 50],
  ['null dimensions use neutral defaults', all(null), 50],
  ['maximum remains 100', all(100), 100],
  ['minimum positive remains 1', all(1), 1],
  ['neutral score remains 50', all(50), 50],
  ...dimensions.map(d => [`${d} contributes one fifth of the score`, { [`score_${d}`]: 100 }, 60]),
  ['rounds down below midpoint', { ...all(50), score_performance: 52 }, 50],
  ['rounds up above midpoint', { ...all(50), score_performance: 53 }, 51],
  ['four missing dimensions remain neutral', { score_performance: 54 }, 51],
  ['uneven dimensions retain their average', { score_performance: 90, score_camera: 60, score_battery: 80, score_display: 70, score_value: 50 }, 70],
  ['uniform 79 remains 79', all(79), 79],
  ['uniform 90 remains 90', all(90), 90],
  ['undefined is treated as missing', all(undefined), 50],
  ['unrelated audio score does not affect card score', { ...all(80), score_audio: 1 }, 80],
  ['unrelated software score does not affect card score', { ...all(70), score_software: 100 }, 70],
];
assert.equal(scoreCases.length, 20);
for (const [name, input, expected] of scoreCases) test(`P11 score: ${name}`, () => {
  const snapshot = { ...input };
  assert.equal(getCatalogScore(input), expected);
  assert.deepEqual(input, snapshot, 'scoring must not mutate its input');
});

// 20 persisted dock contracts, including malformed data and capacity boundaries.
const { sanitizeCompareList } = load('context/CompareContext.js');
const item = (id, price = 1000000) => ({ id, name: `Product ${id}`, price });
for (const [name, value] of [['null', null], ['object', {}], ['string', '[]'], ['number', 42], ['boolean', false], ['undefined', undefined]]) {
  test(`P11 dock: rejects root ${name}`, () => assert.equal(sanitizeCompareList(value).length, 0));
}
const invalidItems = [
  ['missing name', { id: 'a', price: 1 }], ['blank name', { ...item('a'), name: ' ' }],
  ['missing id', { name: 'a', price: 1 }], ['blank id', item(' ')],
  ['null entry', null], ['NaN price', item('a', NaN)],
  ['infinite price', item('a', Infinity)], ['negative price', item('a', -1)],
];
for (const [name, value] of invalidItems) test(`P11 dock: rejects ${name} but keeps valid neighbors`, () => {
  assert.equal(sanitizeCompareList([item('before'), value, item('after')]).map(p => p.id).join(','), 'before,after');
});
test('P11 dock: zero price is retained as a finite nonnegative amount', () => assert.equal(sanitizeCompareList([item('a', 0)])[0].price, 0));
test('P11 dock: one valid product is retained', () => assert.equal(sanitizeCompareList([item('a')])[0].id, 'a'));
test('P11 dock: duplicate ids retain the first product', () => assert.equal(sanitizeCompareList([item('a', 1), item('a', 2)])[0].price, 1));
test('P11 dock: fifth unique product is excluded', () => assert.equal(sanitizeCompareList(['a','b','c','d','e'].map(id => item(id))).map(p => p.id).join(','), 'a,b,c,d'));
test('P11 dock: selection order remains stable', () => assert.equal(sanitizeCompareList(['d','b','a'].map(id => item(id))).map(p => p.id).join(','), 'd,b,a'));
test('P11 dock: validation does not mutate the saved array', () => {
  const input = [null, item('a'), item('a')]; const before = JSON.stringify(input);
  sanitizeCompareList(input); assert.equal(JSON.stringify(input), before);
});

// 15 real budget interactions, one for each category/segment combination.
function find(node, predicate) {
  if (!React.isValidElement(node)) return [];
  return [...(predicate(node) ? [node] : []), ...React.Children.toArray(node.props.children).flatMap(child => find(child, predicate))];
}
const StepBudget = load('components/wizard/StepBudget.js').default;
const budgetCases = {
  smartphone: [[2000000,4500000],[4500000,8000000],[8000000,25000000]],
  laptop: [[5000000,10000000],[10000000,20000000],[20000000,35000000]],
  tablet: [[3000000,7000000],[7000000,15000000],[15000000,25000000]],
  tws: [[300000,1000000],[1000000,2500000],[2500000,5000000]],
  smartwatch: [[1500000,3500000],[3500000,7000000],[7000000,16000000]],
};
for (const [category, presets] of Object.entries(budgetCases)) presets.forEach(([min, max], index) => {
  test(`P11 budget: ${category} segment ${index + 1} applies exact amounts and representable sliders`, () => {
    let actualMin, actualMax;
    const props = { category, budgetMin: 0, budgetMax: 35000000, onChangeMin: v => { actualMin = v; }, onChangeMax: v => { actualMax = v; } };
    find(StepBudget(props), e => e.type === 'button')[index].props.onClick();
    assert.equal(actualMin, min); assert.equal(actualMax, max);
    const ranges = find(StepBudget({ ...props, budgetMin: min, budgetMax: max }), e => e.type === 'input');
    assert.equal(min % ranges[0].props.step, 0); assert.equal(max % ranges[1].props.step, 0);
    ranges[0].props.onChange({ target: { value: max } });
    assert.equal(actualMin, min, 'minimum must not cross maximum');
    ranges[1].props.onChange({ target: { value: min } });
    assert.equal(actualMax, max, 'maximum must not cross minimum');
  });
});

// 20 client API fallback contracts. Fetch is mocked; no service/database/browser.
const scoreAttrs = ['performance','camera','battery','display','build_quality','value','audio','software'];
function fixture(id, name, category, brand, price, score, tags, description = '') {
  return { id, name, category, brand, price, tags, description, specs: {}, warranty: { duration_months: 12, score: 80 },
    ...Object.fromEntries(scoreAttrs.map(d => [`score_${d}`, score])) };
}
const catalog = [
  fixture('a','Alpha Phone','smartphone','Acme',100,90,['gaming'],'fast chip'),
  fixture('b','Beta Laptop','laptop','Bravo',200,80,['office'],'portable'),
  fixture('c','Gamma Phone','smartphone','Acme',300,70,['office','camera'],'large lens'),
  fixture('d','Delta Audio','tws','Delta',50,60,['music'],'compact'),
];
function api(products = catalog) {
  return load('lib/api.js', { '@/data/products': { PRODUCTS: products } }, {
    process: { env: {} }, URLSearchParams, fetch: async () => { throw Error('unit-test offline'); }, console: { warn() {} },
  });
}
const filterCases = [
  ['unfiltered score order', {}, 'a,b,c,d'],
  ['trimmed search', { search: ' Alpha ' }, 'a'],
  ['case-insensitive name search', { search: 'BETA' }, 'b'],
  ['brand search', { search: 'acme' }, 'a,c'],
  ['description search', { search: 'portable' }, 'b'],
  ['tag search', { search: 'music' }, 'd'],
  ['category filter', { category: 'smartphone' }, 'a,c'],
  ['case-insensitive brand filter', { brand: 'ACME' }, 'a,c'],
  ['inclusive minimum price', { min_price: 200 }, 'b,c'],
  ['inclusive maximum price', { max_price: 100 }, 'a,d'],
  ['closed budget range', { min_price: 100, max_price: 200 }, 'a,b'],
  ['single tag filter', { tags: 'camera' }, 'c'],
  ['multiple tags use OR', { tags: ['gaming','music'] }, 'a,d'],
  ['comma tags trim whitespace', { tags: ' office, music ' }, 'b,c,d'],
  ['ascending price', { sort_by: 'price_asc' }, 'd,a,b,c'],
  ['descending price', { sort_by: 'price_desc' }, 'c,b,a,d'],
  ['alphabetical name order', { sort_by: 'name' }, 'a,b,d,c'],
  ['first page', { page: 1, per_page: 2 }, 'a,b'],
  ['second page', { page: 2, per_page: 2 }, 'c,d'],
  ['no matching product', { search: 'unknown' }, ''],
];
for (const [name, params, expected] of filterCases) test(`P11 catalog fallback: ${name}`, async () => {
  const snapshot = JSON.stringify(catalog); const result = await api().getProducts(params);
  assert.equal(result.products.map(p => p.id).join(','), expected);
  assert.equal(result.source, 'fallback'); assert.equal(JSON.stringify(catalog), snapshot);
});

// 20 comparison contracts: ordered selections, numerical units and highlights.
const { PRODUCTS } = load('data/products.js');
for (const ids of [['sm-002','sm-001'],['sm-004','sm-003'],['lp-002','lp-001'],['lp-005','lp-004'],['tb-002','tb-001'],['tw-002','tw-001'],['tw-004','tw-003'],['sw-003','sw-001']]) {
  test(`P11 comparison: preserves selected order ${ids.join(' then ')}`, async () => {
    assert.equal((await api(PRODUCTS).compareProducts(ids)).products.map(p => p.id).join(','), ids.join(','));
  });
}
async function comparison(a = {}, b = {}) {
  const products = [{ ...catalog[0], ...a }, { ...catalog[2], id: 'b', ...b }];
  return api(products).compareProducts(['a','b']);
}
const spec = (result, key) => result.highlights.find(h => h.spec_name === key);
test('P11 comparison: larger RAM wins', async () => assert.equal(spec(await comparison({ specs:{ram:'8 GB'} },{ specs:{ram:'16 GB'} }), 'ram').best_product_id, 'b'));
test('P11 comparison: TB storage is normalized to GB', async () => assert.equal(spec(await comparison({ specs:{storage:'1 TB'} },{ specs:{storage:'512 GB'} }), 'storage').best_product_id, 'a'));
test('P11 comparison: lower weight wins after kg conversion', async () => assert.equal(spec(await comparison({ specs:{weight:'0.15 kg'} },{ specs:{weight:'200 g'} }), 'weight').best_product_id, 'a'));
test('P11 comparison: identical RAM is a shared win', async () => assert.equal(spec(await comparison({ specs:{ram:'8 GB'} },{ specs:{ram:'8 GB'} }), 'ram').is_tie, true));
test('P11 comparison: processor names do not invent numerical winners', async () => assert.equal(spec(await comparison({ specs:{processor:'Chip 10'} },{ specs:{processor:'Chip 5'} }), 'processor').best_product_ids.length, 0));
test('P11 comparison: battery mAh and Wh are not compared', async () => assert.equal(spec(await comparison({ specs:{battery:'4000 mAh'} },{ specs:{battery:'60 Wh'} }), 'battery').best_product_ids.length, 0));
test('P11 comparison: cross-category dimension has no winner', async () => assert.equal(spec(await comparison({}, { category:'laptop' }), 'Skor Kamera').best_product_ids.length, 0));
test('P11 comparison: higher camera dimension wins', async () => assert.equal(spec(await comparison({ score_camera:10 },{ score_camera:90 }), 'Skor Kamera').best_product_id, 'b'));
test('P11 comparison: equal dimension scores expose a tie', async () => assert.equal(spec(await comparison({ score_camera:80 },{ score_camera:80 }), 'Skor Kamera').is_tie, true));
test('P11 comparison: cheaper same-category price wins', async () => assert.equal(spec(await comparison({ price:100 },{ price:200 }), 'Harga (IDR)').best_product_id, 'a'));
test('P11 comparison: higher warranty index wins', async () => assert.equal(spec(await comparison({ warranty:{duration_months:12,score:90} },{ warranty:{duration_months:12,score:60} }), 'Garansi').best_product_id, 'a'));
test('P11 comparison: cross-category summary avoids universal winner', async () => assert.equal((await comparison({}, { category:'laptop' })).win_summary.length, 0));
