const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const { transformSync } = require('next/dist/build/swc');

const sourceRoot = path.resolve(__dirname, '../src');

// Use the installed JSX compiler and actual components without a browser,
// effects, network requests, local .env files, or a database.
function loadSource(entry, overrides = {}, globals = {}) {
  const cache = new Map();
  function load(filename) {
    if (cache.has(filename)) return cache.get(filename).exports;
    const module = { exports: {} };
    cache.set(filename, module);
    const { code } = transformSync(fs.readFileSync(filename, 'utf8'), {
      filename,
      jsc: {
        parser: { syntax: 'ecmascript', jsx: true },
        transform: { react: { runtime: 'classic' } },
      },
      module: { type: 'commonjs' },
    });
    const requireSource = (name) => {
      if (Object.hasOwn(overrides, name)) return overrides[name];
      if (name.startsWith('@/')) return load(path.join(sourceRoot, `${name.slice(2)}.js`));
      if (name.startsWith('.')) return load(path.resolve(path.dirname(filename), `${name}.js`));
      return require(name);
    };
    const evaluate = vm.runInNewContext(`(function(require, module, exports) {${code}\n})`, globals);
    evaluate(requireSource, module, module.exports);
    return module.exports;
  }
  return load(path.join(sourceRoot, entry));
}

function findElements(node, predicate) {
  if (!React.isValidElement(node)) return [];
  const matches = predicate(node) ? [node] : [];
  for (const child of React.Children.toArray(node.props.children)) {
    matches.push(...findElements(child, predicate));
  }
  return matches;
}

const { PRODUCTS } = loadSource('data/products.js');
const product = (id) => PRODUCTS.find((item) => item.id === id);

function renderCatalog(products, states = {}) {
  let stateIndex = 0;
  const values = { 0: products, 1: false, ...states };
  const CatalogPage = loadSource('app/catalog/page.js', {
    react: {
      ...React,
      useState: (initial) => {
        const index = stateIndex++;
        return [Object.hasOwn(values, index) ? values[index] : initial, () => {}];
      },
      useEffect: () => {},
      useMemo: (compute) => compute(),
    },
    '@/lib/api': { getProducts: () => { throw new Error('Unexpected API request'); } },
    '@/context/CompareContext': { useCompare: () => ({ compareList: [], isInCompare: () => false }) },
  }).default;
  const tree = CatalogPage();
  return findElements(tree, (element) => typeof element.type === 'function' && element.props.product)
    .map((element) => ({ product: element.props.product, card: element.type({ product: element.props.product }) }));
}

function displayedScore(card) {
  return findElements(card, (element) => Object.hasOwn(element.props, 'score'))[0].props.score;
}

test('highest-score catalog order follows actual card badges for previously reversed products', () => {
  const samsung = product('sm-001');
  const xiaomi = product('sm-004');
  const cards = renderCatalog([samsung, xiaomi]);
  assert.deepEqual(cards.map((item) => item.product.id), ['sm-004', 'sm-001']);
  assert.deepEqual(cards.map((item) => displayedScore(item.card)), [87, 86]);
});

test('entire local catalog is descending by displayed score and does not mutate input', () => {
  const input = Array.from(PRODUCTS);
  const before = input.map((item) => item.id);
  const cards = renderCatalog(input);
  const scores = cards.map((item) => displayedScore(item.card));
  assert.equal(cards.length, PRODUCTS.length);
  assert.ok(scores.every((score, index) => index === 0 || scores[index - 1] >= score));
  assert.deepEqual(input.map((item) => item.id), before);
});

test('equal rounded card scores use deterministic product ID order', () => {
  const first = { ...product('sm-001'), id: 'tie-a', score_value: 60.1 };
  const second = { ...product('sm-001'), id: 'tie-b', score_value: 60.2 };
  for (const input of [[second, first], [first, second]]) {
    const cards = renderCatalog(input);
    assert.deepEqual(cards.map((item) => item.product.id), ['tie-a', 'tie-b']);
    assert.deepEqual(cards.map((item) => displayedScore(item.card)), [86, 86]);
  }
});

test('card score keeps its existing five-dimension formula, defaults and rounding', () => {
  const { getCatalogScore } = loadSource('lib/catalogScore.js');
  assert.equal(getCatalogScore(product('sm-006')), 79);
  assert.equal(getCatalogScore({}), 50);
  assert.equal(getCatalogScore({ score_performance: 0 }), 50);
  assert.equal(getCatalogScore({ score_performance: 54 }), 51);
});

test('price/name sorting and category, brand, budget and search filters remain available', () => {
  const input = [product('sm-001'), product('sm-005'), product('sm-006')];
  const ids = (states) => renderCatalog(input, states).map((item) => item.product.id);
  assert.deepEqual(ids({ 6: 'price_asc' }), ['sm-005', 'sm-006', 'sm-001']);
  assert.deepEqual(ids({ 6: 'price_desc' }), ['sm-001', 'sm-006', 'sm-005']);
  assert.deepEqual(ids({ 6: 'name' }), ['sm-005', 'sm-006', 'sm-001']);
  assert.deepEqual(ids({
    2: 'Samsung', 3: 'smartphone', 4: 'Samsung', 5: { min: 5000000, max: 10000000 },
  }), ['sm-006']);
});

function comparisonHarness() {
  const states = [];
  const storage = new Map();
  const alerts = [];
  let stateIndex = 0;
  const { CompareProvider } = loadSource('context/CompareContext.js', {
    react: {
      ...React,
      useState: (initial) => {
        const index = stateIndex++;
        if (!(index in states)) states[index] = initial;
        return [states[index], (value) => { states[index] = value; }];
      },
      useEffect: () => {},
    },
  }, {
    localStorage: { setItem: (key, value) => storage.set(key, value) },
    alert: (message) => alerts.push(message),
  });
  function context() {
    stateIndex = 0;
    return CompareProvider({ children: null }).props.value;
  }
  const ProductCard = loadSource('components/catalog/ProductCard.js', {
    '@/context/CompareContext': { useCompare: context },
  }).default;
  function card(item) {
    const tree = ProductCard({ product: item });
    const button = findElements(tree, (element) => element.type === 'button' &&
      Object.hasOwn(element.props, 'aria-pressed'))[0];
    assert.ok(button, 'Compare toggle must expose its selected state');
    return { tree, button };
  }
  return { context, card, storage, alerts };
}

test('actual card button adds/removes through the real context and updates labels and selected state', () => {
  const harness = comparisonHarness();
  const item = product('sm-005');
  let { tree, button } = harness.card(item);
  assert.equal(button.props['aria-pressed'], false);
  assert.equal(button.props['aria-label'], `Tambah ke komparasi: ${item.name}`);
  assert.match(renderToStaticMarkup(tree), />Tambah ke komparasi<\/span>/);
  button.props.onClick();
  assert.equal(harness.context().compareList[0].id, item.id);
  ({ tree, button } = harness.card(item));
  assert.equal(button.props['aria-pressed'], true);
  assert.equal(button.props['aria-label'], `Hapus dari komparasi: ${item.name}`);
  assert.match(renderToStaticMarkup(tree), /aria-pressed="true"/);
  assert.match(renderToStaticMarkup(tree), />Hapus dari komparasi<\/span>/);
  button.props.onClick();
  assert.equal(harness.context().compareList.length, 0);
  assert.equal(harness.card(item).button.props['aria-pressed'], false);
  assert.equal(harness.storage.get('comparebuy_dock'), '[]');
});

test('four-product limit, removal at capacity and product detail action retain existing behavior', () => {
  const harness = comparisonHarness();
  for (const item of PRODUCTS.slice(0, 4)) harness.card(item).button.props.onClick();
  harness.card(PRODUCTS[4]).button.props.onClick();
  assert.equal(harness.context().compareList.length, 4);
  assert.equal(harness.alerts.length, 1);
  harness.card(PRODUCTS[0]).button.props.onClick();
  assert.equal(harness.context().compareList.length, 3);
  const { tree } = harness.card(PRODUCTS[1]);
  const detail = findElements(tree, (element) => element.type === 'button' &&
    !Object.hasOwn(element.props, 'aria-pressed'))[0];
  detail.props.onClick();
  assert.equal(harness.context().activeProductModal.id, PRODUCTS[1].id);
  assert.equal(harness.context().compareList.length, 3);
});
