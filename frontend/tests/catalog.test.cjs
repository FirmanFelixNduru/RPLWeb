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

function catalogTree(products, states = {}, onStateChange = () => {}) {
  let stateIndex = 0;
  const values = { 0: products, 1: false, ...states };
  const CatalogPage = loadSource('app/catalog/page.js', {
    react: {
      ...React,
      useState: (initial) => {
        const index = stateIndex++;
        return [Object.hasOwn(values, index) ? values[index] : initial,
          (value) => onStateChange(index, value)];
      },
      useEffect: () => {},
      useMemo: (compute) => compute(),
      useRef: (current) => ({ current }),
    },
    'next/navigation': { usePathname: () => '/catalog' },
    '@/lib/api': { getProducts: () => { throw new Error('Unexpected API request'); } },
    '@/context/CompareContext': { useCompare: () => ({ compareList: [], isInCompare: () => false }) },
  }).default;
  return CatalogPage();
}

function renderCatalog(products, states = {}) {
  const tree = catalogTree(products, states);
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
  detail.props.onClick({ currentTarget: { focus: () => {} } });
  assert.equal(harness.context().activeProductModal.id, PRODUCTS[1].id);
  assert.equal(harness.context().compareList.length, 3);
});

function textContent(node) {
  if (typeof node === 'string' || typeof node === 'number') return String(node);
  if (!React.isValidElement(node)) return '';
  return React.Children.toArray(node.props.children).map(textContent).join('');
}

test('search has a name and its named clear button retains input/clear behavior', () => {
  const SearchBar = loadSource('components/catalog/SearchBar.js').default;
  const calls = [];
  const props = {
    value: 'Samsung', onChange: (value) => calls.push(value), onClear: () => calls.push('clear'),
  };
  const tree = SearchBar(props);
  const input = findElements(tree, (node) => node.type === 'input')[0];
  const clear = findElements(tree, (node) => node.type === 'button')[0];
  assert.equal(input.props['aria-label'], 'Cari gadget');
  assert.equal(clear.props['aria-label'], 'Hapus pencarian');
  input.props.onChange({ target: { value: 'POCO' } });
  clear.props.onClick();
  assert.deepEqual(calls, ['POCO', 'clear']);
  assert.equal(findElements(SearchBar({ ...props, value: '' }), (node) => node.type === 'button').length, 0);
});

function filterTree(overrides = {}) {
  const FilterPanel = loadSource('components/catalog/FilterPanel.js').default;
  return FilterPanel({
    selectedCategory: 'smartphone', selectedBrand: 'Samsung',
    selectedPriceRange: { min: 5000000, max: 15000000 }, sortBy: 'price_asc',
    brands: ['Samsung', 'Xiaomi'], totalFound: 6,
    ...overrides,
  });
}

function budgetPresets() {
  const presets = [];
  const tree = filterTree({ onSelectPriceRange: (range) => presets.push(range) });
  const group = findElements(tree, (node) => node.props['aria-label'] === 'Rentang Anggaran (Budget)')[0];
  for (const button of findElements(group, (node) => node.type === 'button')) button.props.onClick();
  return presets;
}

function budgetRemoveButton(tree) {
  return findElements(tree, (node) => node.type === 'button' &&
    node.props['aria-label']?.startsWith('Hapus filter anggaran:'))[0];
}

test('default budget does not render a budget chip or an empty active-filter summary', () => {
  for (const range of [{ min: 0, max: null }, budgetPresets()[0]]) {
    const tree = catalogTree(Array.from(PRODUCTS), { 5: range });
    assert.equal(budgetRemoveButton(tree), undefined);
    assert.equal(textContent(tree).includes('Filter Aktif:'), false);
  }
});

for (const label of ['< Rp 5 Juta', 'Rp 5 - 15 Juta', 'Rp 15 - 25 Juta', '> Rp 25 Juta']) {
  test(`active budget summary uses the actual filter preset label: ${label}`, () => {
    const range = budgetPresets().find((preset) => preset.label === label);
    assert.ok(range);
    const tree = catalogTree(Array.from(PRODUCTS), { 5: range });
    assert.ok(textContent(tree).includes(`Anggaran: ${label}`));
    const remove = budgetRemoveButton(tree);
    assert.equal(remove.props['aria-label'], `Hapus filter anggaran: ${label}`);
    assert.equal(remove.props.type, 'button');
    assert.match(remove.props.className, /focus-visible:outline/);
    assert.match(remove.props.className, /min-w-\[44px\]/);
    assert.match(remove.props.className, /min-h-\[44px\]/);
  });
}

test('removing budget changes only budget state and moves focus to the existing search input', () => {
  const calls = [], focusCalls = [];
  const states = { 2: 'Galaxy', 3: 'smartphone', 4: 'Samsung', 5: budgetPresets()[2], 6: 'price_asc' };
  const tree = catalogTree(Array.from(PRODUCTS), states, (index, value) => calls.push([index, value]));
  const searchContainer = findElements(tree, (node) => node.type === 'div' &&
    node.props.className === 'w-full max-w-3xl')[0];
  searchContainer.ref.current = {
    querySelector: (selector) => {
      assert.equal(selector, 'input');
      return { focus: (options) => focusCalls.push(options.preventScroll) };
    },
  };
  budgetRemoveButton(tree).props.onClick();
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], 5);
  assert.equal(calls[0][1].min, 0);
  assert.equal(calls[0][1].max, null);
  assert.deepEqual(focusCalls, [true]);
  const cleared = catalogTree(Array.from(PRODUCTS), { ...states, 5: calls[0][1] });
  assert.equal(budgetRemoveButton(cleared), undefined);
  for (const label of ['Hapus filter kategori: smartphone', 'Hapus filter merek: Samsung', 'Hapus filter pencarian']) {
    assert.ok(findElements(cleared, (node) => node.props['aria-label'] === label).length);
  }
  const panel = findElements(cleared, (node) => typeof node.type === 'function' && node.props.onSelectSort)[0];
  assert.equal(panel.props.sortBy, 'price_asc');
});

test('upper-unbounded budget stays open until explicit completion and remains summarized after closing', () => {
  const states = { 7: true };
  const tree = catalogTree(Array.from(PRODUCTS), states, (index, value) => { states[index] = value; });
  const panels = findElements(tree, (node) => typeof node.type === 'function' && node.props.onSelectPriceRange);
  panels.at(-1).props.onSelectPriceRange(budgetPresets().at(-1));
  assert.equal(states[7], true);
  const open = catalogTree(Array.from(PRODUCTS), states, (index, value) => { states[index] = value; });
  findElements(open, (node) => node.type === 'button' && textContent(node).startsWith('Lihat hasil ('))[0].props.onClick();
  assert.equal(states[7], false);
  const closed = catalogTree(Array.from(PRODUCTS), states);
  assert.equal(findElements(closed, (node) => node.type === 'dialog').length, 0);
  assert.equal(budgetRemoveButton(closed).props['aria-label'], 'Hapus filter anggaran: > Rp 25 Juta');
});

function mobileFilterPanel(tree) {
  const dialog = findElements(tree, (node) => node.type === 'dialog')[0];
  return findElements(dialog, (node) => typeof node.type === 'function' && node.props.onSelectCategory)[0];
}

for (const [handler, value, index] of [
  ['onSelectCategory', 'laptop', 3],
  ['onSelectBrand', 'Lenovo', 4],
  ['onSelectPriceRange', budgetPresets().at(-1), 5],
]) {
  test(`mobile ${handler} changes only its filter without closing the dialog`, () => {
    const calls = [];
    const tree = catalogTree(Array.from(PRODUCTS), { 7: true }, (i, next) => calls.push([i, next]));
    mobileFilterPanel(tree).props[handler](value);
    assert.equal(calls.length, 1);
    assert.equal(calls[0][0], index);
    assert.equal(calls[0][1], value);
  });
}

test('mobile filter session applies consecutive choices immediately, preserves search/sort and completes explicitly', () => {
  const states = { 2: 'Galaxy', 7: true }, calls = [];
  const render = () => catalogTree(Array.from(PRODUCTS), states, (i, value) => { states[i] = value; calls.push(i); });
  for (const [handler, value] of [
    ['onSelectCategory', 'smartphone'], ['onSelectBrand', 'Samsung'],
    ['onSelectPriceRange', budgetPresets()[2]], ['onSelectSort', 'price_asc'],
  ]) {
    mobileFilterPanel(render()).props[handler](value);
    assert.equal(states[7], true);
    const tree = render();
    const count = renderCatalog(Array.from(PRODUCTS), states).length;
    assert.equal(mobileFilterPanel(tree).props.totalFound, count);
    const done = findElements(tree, (node) => node.type === 'button' && textContent(node).startsWith('Lihat hasil ('))[0];
    assert.equal(textContent(done), `Lihat hasil (${count} produk)`);
    assert.equal(done.props.type, 'button');
    assert.equal(done.props.disabled, undefined);
  }
  assert.equal(states[2], 'Galaxy');
  const expected = Array.from(PRODUCTS).filter((p) => p.category === 'smartphone' && p.brand === 'Samsung' &&
    p.name.includes('Galaxy') && p.price >= 5000000 && p.price <= 15000000).sort((a, b) => a.price - b.price);
  assert.ok(expected.length > 0);
  assert.deepEqual(renderCatalog(Array.from(PRODUCTS), states).map((item) => item.product.id), expected.map((p) => p.id));
  const tree = render(), done = findElements(tree, (node) => node.type === 'button' && textContent(node).startsWith('Lihat hasil ('))[0];
  calls.length = 0;
  done.props.onClick();
  assert.deepEqual(calls, [7]);
  assert.equal(states[7], false);
  assert.ok(budgetRemoveButton(render()));
  const selectedRange = states[5];
  states[7] = true;
  const reopened = mobileFilterPanel(render());
  assert.equal(reopened.props.selectedCategory, 'smartphone');
  assert.equal(reopened.props.selectedBrand, 'Samsung');
  assert.equal(reopened.props.selectedPriceRange, selectedRange);
  assert.equal(reopened.props.sortBy, 'price_asc');
  calls.length = 0;
  findElements(render(), (node) => node.props['aria-label'] === 'Tutup filter dan pengurutan')[0].props.onClick();
  assert.deepEqual(calls, [7]);
  assert.equal(states[5], selectedRange);
});

test('zero-result completion stays enabled, reset stays open and the completion action is last in the dialog', () => {
  const states = { 2: 'no-product-matches-this-query', 3: 'laptop', 4: 'Lenovo', 5: budgetPresets().at(-1), 6: 'name', 7: true };
  const render = () => catalogTree(Array.from(PRODUCTS), states, (i, value) => { states[i] = value; });
  const tree = render(), dialog = findElements(tree, (node) => node.type === 'dialog')[0];
  const buttons = findElements(dialog, (node) => node.type === 'button');
  const done = buttons.at(-1);
  assert.equal(textContent(done), 'Lihat hasil (0 produk)');
  assert.equal(done.props.disabled, undefined);
  assert.match(done.props.className, /min-h-\[44px\]/);
  assert.match(done.props.className, /focus-visible:outline/);
  assert.ok(textContent(dialog).includes('Perubahan filter langsung diterapkan.'));
  done.props.onClick();
  assert.equal(states[7], false);
  assert.equal(states[2], 'no-product-matches-this-query');
  states[7] = true;
  mobileFilterPanel(render()).props.onResetFilters();
  assert.equal(states[7], true);
  assert.equal(states[2], '');
  assert.equal(states[3], '');
  assert.equal(states[4], '');
  assert.equal(states[5].min, 0);
  assert.equal(states[5].max, null);
  assert.equal(states[6], 'score');
  assert.equal(mobileFilterPanel(render()).props.totalFound, PRODUCTS.length);
  assert.equal(textContent(findElements(render(), (node) => node.type === 'button' && textContent(node).startsWith('Lihat hasil ('))[0]), `Lihat hasil (${PRODUCTS.length} produk)`);
});

test('budget removal preserves combined category, brand, search and price sorting results', () => {
  const states = { 2: 'Galaxy', 3: 'smartphone', 4: 'Samsung', 5: budgetPresets()[2], 6: 'price_asc' };
  const expected = (range) => Array.from(PRODUCTS).filter((p) => p.category === 'smartphone' &&
    p.brand === 'Samsung' && p.name.includes('Galaxy') && p.price >= range.min &&
    (range.max === null || p.price <= range.max)).sort((a, b) => a.price - b.price).map((p) => p.id);
  assert.deepEqual(renderCatalog(Array.from(PRODUCTS), states).map((item) => item.product.id), expected(states[5]));
  const tree = catalogTree(Array.from(PRODUCTS), states, (index, value) => { states[index] = value; });
  budgetRemoveButton(tree).props.onClick();
  assert.deepEqual(renderCatalog(Array.from(PRODUCTS), states).map((item) => item.product.id), expected({ min: 0, max: null }));
  assert.ok(renderCatalog(Array.from(PRODUCTS), states).length > 0);
});

test('reset still clears all filters and restores score sorting after an active budget', () => {
  const states = { 2: 'Galaxy', 3: 'smartphone', 4: 'Samsung', 5: budgetPresets().at(-1), 6: 'name' };
  const tree = catalogTree(Array.from(PRODUCTS), states, (index, value) => { states[index] = value; });
  findElements(tree, (node) => typeof node.type === 'function' && node.props.onResetFilters)[0].props.onResetFilters();
  assert.equal(states[2], '');
  assert.equal(states[3], '');
  assert.equal(states[4], '');
  assert.equal(states[5].min, 0);
  assert.equal(states[5].max, null);
  assert.equal(states[6], 'score');
  assert.equal(budgetRemoveButton(catalogTree(Array.from(PRODUCTS), states)), undefined);
  assert.equal(renderCatalog(Array.from(PRODUCTS), states).length, PRODUCTS.length);
});

test('each filter group exposes one selected option and preserves selection callbacks', () => {
  const calls = [];
  const tree = filterTree({
    onSelectCategory: (value) => calls.push(['category', value]),
    onSelectBrand: (value) => calls.push(['brand', value]),
    onSelectPriceRange: (value) => calls.push(['price', value.min, value.max]),
  });
  const groups = findElements(tree, (node) => node.props.role === 'group');
  assert.deepEqual(groups.map((node) => node.props['aria-label']),
    ['Kategori Gadget', 'Merek / Brand', 'Rentang Anggaran (Budget)']);
  for (const group of groups) {
    const buttons = findElements(group, (node) => node.type === 'button');
    assert.equal(buttons.filter((node) => node.props['aria-pressed'] === true).length, 1);
    assert.ok(buttons.every((node) => typeof node.props['aria-pressed'] === 'boolean'));
    const selected = buttons.find((node) => node.props['aria-pressed']);
    assert.ok(findElements(selected, (node) => node.props['aria-hidden'] === 'true').length > 0);
  }
  const buttons = findElements(tree, (node) => node.type === 'button');
  buttons.find((node) => textContent(node) === 'Laptop').props.onClick();
  buttons.find((node) => textContent(node) === 'Xiaomi').props.onClick();
  buttons.find((node) => textContent(node) === '> Rp 25 Juta').props.onClick();
  assert.deepEqual(calls, [['category', 'laptop'], ['brand', 'Xiaomi'], ['price', 25000000, null]]);
  const cleared = filterTree({ selectedCategory: '', selectedBrand: '', selectedPriceRange: { min: 0, max: null } });
  const chosen = findElements(cleared, (node) => node.type === 'button' && node.props['aria-pressed']);
  assert.deepEqual(chosen.map(textContent), ['Semua', 'Semua Brand', 'Semua Budget']);
});

test('sort select is enclosed by its label and sort/reset handlers retain their values', () => {
  const calls = [];
  const tree = filterTree({ onSelectSort: (value) => calls.push(value), onResetFilters: () => calls.push('reset') });
  const label = findElements(tree, (node) => node.type === 'label')[0];
  assert.ok(textContent(label).startsWith('Urutkan Berdasarkan'));
  const select = findElements(label, (node) => node.type === 'select')[0];
  assert.equal(select.props.value, 'price_asc');
  select.props.onChange({ target: { value: 'name' } });
  findElements(tree, (node) => node.props['aria-label'] === 'Reset semua filter dan pengurutan')[0].props.onClick();
  assert.deepEqual(calls, ['name', 'reset']);
});

test('mobile toggle, close control and filter chips have names and preserve existing state updates', () => {
  const calls = [];
  const tree = catalogTree(Array.from(PRODUCTS), {
    2: 'Samsung', 3: 'smartphone', 4: 'Samsung', 7: true,
  }, (index, value) => calls.push([index, value]));
  const toggle = findElements(tree, (node) => node.type === 'button' && Object.hasOwn(node.props, 'aria-expanded'))[0];
  assert.equal(toggle.props['aria-expanded'], true);
  assert.ok(findElements(tree, (node) => node.props.id === toggle.props['aria-controls']).length > 0);
  findElements(tree, (node) => node.props['aria-label'] === 'Tutup filter dan pengurutan')[0].props.onClick();
  for (const name of ['Hapus filter kategori: smartphone', 'Hapus filter merek: Samsung', 'Hapus filter pencarian']) {
    findElements(tree, (node) => node.props['aria-label'] === name)[0].props.onClick();
  }
  assert.deepEqual(calls, [[7, false], [3, ''], [4, ''], [2, '']]);
  const closed = catalogTree([]);
  assert.equal(findElements(closed, (node) => node.props.id === 'catalog-mobile-filters').length, 0);
  assert.equal(findElements(closed, (node) => Object.hasOwn(node.props, 'aria-expanded'))[0].props['aria-expanded'], false);
});

for (const name of [
  'Xiaomi 14 Ultra',
  'Lenovo ThinkPad X1 Carbon Gen 11',
  'ASUS ROG Zephyrus G14 (2024)',
  'Fixture Laptop Professional Edition Generasi 2026 Model ABC 123 Konfigurasi RAM 32 GB Storage 2 TB untuk Pengujian Nama Sangat Panjang Tanpa Mengubah Dataset',
]) {
  test(`product heading preserves its complete name and natural wrapping: ${name}`, () => {
    const item = { ...product('lp-005'), name };
    const harness = comparisonHarness();
    const { tree } = harness.card(item);
    const heading = findElements(tree, (node) => node.type === 'h3')[0];
    assert.equal(textContent(heading), name);
    assert.equal(heading.props.onClick, undefined);
    assert.equal(heading.props.tabIndex, undefined);
    assert.equal(heading.props.title, undefined);
    assert.doesNotMatch(heading.props.className, /line-clamp|truncate|whitespace-nowrap|(?:^|\s)(?:min-|max-)?h-/);
    assert.equal(heading.props.style, undefined);
    const compare = findElements(tree, (node) => node.type === 'button' &&
      node.props['aria-label'] === `Tambah ke komparasi: ${name}`)[0];
    assert.equal(compare.props.type, 'button');
    compare.props.onClick();
    assert.equal(harness.context().compareList[0].name, name);
    const selected = harness.card(item).tree;
    const remove = findElements(selected, (node) => node.props['aria-label'] === `Hapus dari komparasi: ${name}`)[0];
    assert.equal(remove.props['aria-pressed'], true);
    remove.props.onClick();
    assert.equal(harness.context().compareList.length, 0);
    const detail = findElements(tree, (node) => node.type === 'button' && textContent(node) === 'Lihat Detail')[0];
    assert.equal(detail.props.type, 'button');
    const trigger = { focus: () => {} };
    detail.props.onClick({ currentTarget: trigger });
    assert.equal(harness.context().activeProductModal.name, name);
  });
}

test('product name is a noninteractive heading while detail remains a keyboard-native button', () => {
  const harness = comparisonHarness();
  const { tree } = harness.card(product('sm-001'));
  const heading = findElements(tree, (node) => node.type === 'h3')[0];
  assert.equal(heading.props.onClick, undefined);
  assert.equal(heading.props.tabIndex, undefined);
  const detail = findElements(tree, (node) => node.type === 'button' && textContent(node) === 'Lihat Detail')[0];
  assert.equal(detail.props.type, 'button');
  detail.props.onClick({ currentTarget: { focus: () => {} } });
  assert.equal(harness.context().activeProductModal.id, 'sm-001');
});

const colors = require('tailwindcss/colors');
function colorToken(token) {
  const [family, shade] = token.split('-');
  const hex = shade ? colors[family]?.[shade] : colors[family];
  if (typeof hex !== 'string' || !hex.startsWith('#')) return null;
  const expanded = hex.length === 4 ? '#' + hex.slice(1).split('').map((x) => x + x).join('') : hex;
  return expanded.slice(1).match(/../g).map((value) => parseInt(value, 16) / 255);
}

// Resolve the actual rendered utility colors; alpha is composited against the
// known parent surface. This is source-based color math, not a browser capture.
function classColor(className, role, dark = false, parent = [1, 1, 1]) {
  const tokens = className.split(/\s+/);
  const get = (prefix) => tokens.map((token) => {
    if (!token.startsWith(prefix)) return null;
    const [name, opacity = '100'] = token.slice(prefix.length).split('/');
    const rgb = colorToken(name);
    return rgb && rgb.map((value, index) => value * Number(opacity) / 100 + parent[index] * (1 - Number(opacity) / 100));
  }).filter(Boolean).at(-1);
  return (dark && get(`dark:${role}-`)) || get(`${role}-`);
}

function contrast(foreground, background) {
  assert.ok(foreground && background, 'Color must resolve to an installed palette value');
  const luminance = (rgb) => rgb.map((v) => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4)
    .reduce((sum, v, index) => sum + v * [0.2126, 0.7152, 0.0722][index], 0);
  const a = luminance(foreground), b = luminance(background);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

test('metadata, rating, filter count, empty state and search placeholder meet normal-text contrast in both themes', () => {
  const { tree: card } = comparisonHarness().card(product('sm-001'));
  const metadata = findElements(card, (node) => node.type === 'span' && textContent(node) === 'Harga katalog')[0];
  const rating = findElements(card, (node) => React.Children.toArray(node.props.children)
    .some((child) => child.props?.children === product('sm-001').review_sentiment.overall_score))[0];
  const count = findElements(card, (node) => node.props.className?.includes('font-normal') && textContent(node).startsWith('('))[0];
  const filters = filterTree();
  const filterCount = findElements(filters, (node) => node.type === 'span' && textContent(node) === '(6 Produk)')[0];
  const empty = findElements(catalogTree([]), (node) => node.type === 'p' && textContent(node).startsWith('Coba ubah'))[0];
  const SearchBar = loadSource('components/catalog/SearchBar.js').default;
  const search = findElements(SearchBar({ value: '' }), (node) => node.type === 'input')[0];
  for (const dark of [false, true]) {
    const surface = classColor(card.props.className, 'bg', dark);
    for (const node of [metadata, rating, count, filterCount, empty]) {
      const foreground = classColor(node.props.className, 'text', dark);
      assert.ok(foreground, `Text color missing: ${node.props.className}`);
      assert.ok(contrast(foreground, surface) >= 4.5, textContent(node));
    }
    const searchBg = classColor(search.props.className, 'bg', dark);
    const placeholder = classColor(search.props.className, dark ? 'dark:placeholder:text' : 'placeholder:text');
    assert.ok(contrast(placeholder, searchBg) >= 4.5);
    assert.ok(contrast(classColor(search.props.className, 'border', dark), searchBg) >= 3);
  }
});

test('all score badge gradients retain scores and meet contrast across sampled sRGB interpolation', () => {
  const ScoreBadge = loadSource('components/ui/ScoreBadge.js').default;
  for (const score of [95, 85, 75, 65]) {
    const tree = ScoreBadge({ score });
    const badge = findElements(tree, (node) => node.props.className?.includes('bg-gradient-to-r'))[0];
    const start = classColor(badge.props.className, 'from');
    const end = classColor(badge.props.className, 'to');
    const ink = classColor(badge.props.className, 'text');
    assert.ok(findElements(badge, (node) => node.props.children === score).length > 0);
    const scale = findElements(badge, (node) => node.props.children === '/100')[0];
    assert.ok(!scale.props.className.includes('opacity-'));
    for (let step = 0; step <= 100; step++) {
      const background = start.map((value, index) => value + (end[index] - value) * step / 100);
      assert.ok(contrast(ink, background) >= 4.5, `Badge ${score} at ${step}%`);
    }
  }
});

test('catalog controls retain visible focus and 44px targets, with contrast for controls and rating icons', () => {
  const harness = comparisonHarness();
  const item = product('sm-001');
  const unselected = harness.card(item);
  unselected.button.props.onClick();
  const selected = harness.card(item);
  const SearchBar = loadSource('components/catalog/SearchBar.js').default;
  const search = SearchBar({ value: 'Samsung' });
  const filters = filterTree();
  const catalog = catalogTree([], { 2: 'Samsung', 3: 'smartphone', 4: 'Samsung', 7: true });
  for (const tree of [search, filters, catalog, unselected.tree, selected.tree]) {
    const controls = findElements(tree, (node) => ['button', 'input', 'select'].includes(node.type));
    assert.ok(controls.length > 0);
    for (const node of controls) {
      const classes = node.props.className;
      assert.ok(classes.includes('min-h-[44px]'), textContent(node) || node.props['aria-label']);
      assert.ok(classes.includes('focus-visible:outline-2') || classes.includes('focus:ring-2'));
      const role = node.type === 'button' ? 'focus-visible:outline' : 'focus:ring';
      for (const dark of [false, true]) {
        const surface = colorToken(dark ? 'slate-900' : 'white');
        assert.ok(contrast(classColor(classes, role, dark), surface) >= 3);
      }
    }
  }
  const select = findElements(filters, (node) => node.type === 'select')[0];
  const star = findElements(unselected.tree, (node) => node.props.className?.includes('fill-current'))[0];
  const detail = findElements(unselected.tree, (node) => node.type === 'button' && textContent(node) === 'Lihat Detail')[0];
  for (const dark of [false, true]) {
    const surface = colorToken(dark ? 'slate-900' : 'white');
    const selectBg = classColor(select.props.className, 'bg', dark);
    assert.ok(contrast(classColor(select.props.className, 'border', dark), selectBg) >= 3);
    assert.ok(contrast(classColor(star.props.className, 'text', dark), surface) >= 3);
    for (const button of [selected.button, detail]) {
      const ink = classColor(button.props.className, 'text', dark);
      assert.ok(contrast(ink, classColor(button.props.className, 'bg', dark)) >= 4.5);
      assert.ok(contrast(ink, classColor(button.props.className, 'hover:bg', dark)) >= 4.5);
    }
  }
});

test('product and mobile filter expose named native modal dialogs and explicit close actions', () => {
  const calls = [];
  const ProductModal = loadSource('components/product/ProductModal.js', {
    react: { ...React, useState: () => ['specs', () => {}] },
    '@/lib/api': { getLiveMarketplacePrices: () => { throw new Error('Unexpected API request'); } },
    '@/lib/useModalDialog': { useModalDialog: () => ({ dialogRef: { current: null }, titleRef: { current: null } }) },
    '@/context/CompareContext': { useCompare: () => ({
      activeProductModal: product('sm-001'), isInCompare: () => false,
      closeProductModal: () => calls.push('product'),
    }) },
  }).default;
  const productDialog = ProductModal();
  const filterDialog = findElements(catalogTree([], { 7: true }, (index, value) => calls.push([index, value])),
    (node) => node.type === 'dialog')[0];
  for (const dialog of [productDialog, filterDialog]) {
    assert.equal(dialog.type, 'dialog');
    assert.equal(dialog.props.role, 'dialog');
    assert.equal(dialog.props['aria-modal'], 'true');
    assert.equal(dialog.props.open, undefined, 'Open through showModal(), not a non-modal open attribute');
    const title = findElements(dialog, (node) => node.props.id === dialog.props['aria-labelledby'])[0];
    assert.ok(textContent(title).length > 0);
    assert.equal(title.props.tabIndex, -1);
    assert.ok(title.ref);
  }
  findElements(productDialog, (node) => node.props['aria-label'] === 'Tutup Modal')[0].props.onClick();
  findElements(filterDialog, (node) => node.props['aria-label'] === 'Tutup filter dan pengurutan')[0].props.onClick();
  assert.deepEqual(calls, ['product', [7, false]]);
});

test('product and filter openers establish the clicked button as the return-focus target', () => {
  const calls = [];
  const trigger = { focus: (options) => calls.push(options.preventScroll) };
  const harness = comparisonHarness();
  const card = harness.card(product('sm-001')).tree;
  findElements(card, (node) => node.type === 'button' && textContent(node) === 'Lihat Detail')[0]
    .props.onClick({ currentTarget: trigger });
  assert.equal(harness.context().activeProductModal.id, 'sm-001');
  const catalog = catalogTree([], {}, (index, value) => calls.push([index, value]));
  findElements(catalog, (node) => Object.hasOwn(node.props, 'aria-expanded'))[0]
    .props.onClick({ currentTarget: trigger });
  assert.deepEqual(calls, [true, true, [7, true]]);
});

// Execute the actual hook's effect setup/cleanup against stubbed browser APIs.
// This verifies our lifecycle contract, NOT native inertness, Escape key dispatch,
// browser tab order, a focus trap, layout, or screen-reader behavior.
function modalLifecycleEnvironment(overflow = '', priority = '') {
  let value = overflow, importance = priority, currentSession;
  const document = {
    body: { style: {
      getPropertyValue: () => value,
      getPropertyPriority: () => importance,
      setProperty: (name, next, nextPriority = '') => { value = next; importance = nextPriority; },
      removeProperty: () => { value = ''; importance = ''; },
    } },
  };
  let pathname = '/catalog';
  const { useModalDialog } = loadSource('lib/useModalDialog.js', {
    react: {
      useRef: (initial) => currentSession.ref(initial),
      useEffect: (setup, deps) => currentSession.effects.push({ setup, deps }),
    },
    'next/navigation': { usePathname: () => pathname },
  }, { document, getComputedStyle: (node) => ({ visibility: node.cssHidden ? 'hidden' : 'visible' }) });
  const element = () => ({
    isConnected: true, visible: true, inert: false, focused: 0, tabIndex: 0, disabled: false,
    matches() { return this.disabled; },
    closest() { return this.inert ? {} : null; },
    getClientRects() { return this.visible ? [{}] : []; },
    focus(options) { this.focused++; this.options = options; document.activeElement = this; },
  });
  function session() {
    const refs = [];
    let index = 0;
    const trigger = element(), title = element();
    const listeners = new Map();
    const dialog = {
      open: false, shown: 0, closed: 0,
      controls: [],
      querySelectorAll() { return this.controls; },
      contains(node) { return node === title || this.controls.includes(node); },
      showModal() { this.open = true; this.shown++; },
      close() { this.open = false; this.closed++; },
      addEventListener: (name, listener) => listeners.set(name, listener),
      removeEventListener: (name, listener) => {
        assert.equal(listeners.get(name), listener);
        listeners.delete(name);
      },
    };
    const state = {
      effects: [],
      ref(initial) { const i = index++; return refs[i] ||= { current: initial }; },
    };
    return {
      trigger, title, dialog, listeners,
      render(open, onClose) {
        currentSession = state;
        index = 0;
        state.effects = [];
        const result = useModalDialog(open, onClose);
        result.dialogRef.current = dialog;
        result.titleRef.current = title;
        state.effects[0].setup(); // latest onClose callback
        return state.effects[1].setup;
      },
    };
  }
  return {
    document, session, element,
    overflow: () => [value, importance],
    route: (next) => { pathname = next; },
  };
}

test('dialog lifecycle requests native modality, title focus, scroll lock and cleans up on close/unmount', () => {
  const env = modalLifecycleEnvironment('auto', 'important');
  const modal = env.session();
  env.document.activeElement = modal.trigger;
  assert.equal(modal.render(false, () => {})(), undefined);
  assert.equal(modal.dialog.shown, 0);
  const cleanup = modal.render(true, () => {})();
  assert.equal(modal.dialog.shown, 1);
  assert.equal(modal.title.focused, 1);
  assert.equal(modal.title.options.preventScroll, true);
  assert.equal(env.document.activeElement, modal.title);
  assert.deepEqual(env.overflow(), ['hidden', '']);
  assert.deepEqual([...modal.listeners.keys()], ['cancel', 'close', 'keydown']);
  cleanup();
  assert.equal(modal.dialog.open, false);
  assert.equal(modal.dialog.closed, 1);
  assert.equal(modal.listeners.size, 0);
  assert.equal(env.document.activeElement, modal.trigger);
  assert.equal(modal.trigger.options.preventScroll, true);
  assert.deepEqual(env.overflow(), ['auto', 'important']);
});

test('native cancel/close request the latest React close callback without stale Strict Mode close events', () => {
  const env = modalLifecycleEnvironment();
  const modal = env.session();
  const calls = [];
  env.document.activeElement = modal.trigger;
  let cleanup = modal.render(true, () => calls.push('old'))();
  modal.render(true, () => calls.push('current'));
  modal.listeners.get('cancel')({ preventDefault: () => calls.push('prevent') });
  assert.deepEqual(calls, ['prevent', 'current']);
  cleanup();
  cleanup = modal.render(true, () => calls.push('reopened'))();
  modal.listeners.get('close')(); // late close event while the dialog is open again
  assert.equal(calls.length, 2);
  modal.dialog.open = false;
  modal.listeners.get('close')();
  assert.deepEqual(calls, ['prevent', 'current', 'reopened']);
  cleanup();
  assert.deepEqual(env.overflow(), ['', '']);
  assert.equal(modal.listeners.size, 0);
});

test('route change closes React state and does not reopen the previous route dialog', () => {
  const env = modalLifecycleEnvironment();
  const modal = env.session();
  let closed = 0;
  env.document.activeElement = modal.trigger;
  const cleanup = modal.render(true, () => closed++)();
  env.route('/compare');
  cleanup();
  assert.equal(modal.render(true, () => closed++)(), undefined);
  assert.equal(closed, 1);
  assert.equal(modal.dialog.shown, 1);
  assert.equal(modal.listeners.size, 0);
  assert.deepEqual(env.overflow(), ['', '']);
  modal.render(false, () => {})();
  const nextCleanup = modal.render(true, () => {})();
  assert.equal(modal.dialog.shown, 2);
  nextCleanup();
});

test('cleanup skips missing, hidden or explicitly inert return-focus targets', () => {
  for (const state of ['missing', 'hidden', 'inert']) {
    const env = modalLifecycleEnvironment();
    const modal = env.session();
    env.document.activeElement = modal.trigger;
    const cleanup = modal.render(true, () => {})();
    if (state === 'missing') modal.trigger.isConnected = false;
    if (state === 'hidden') modal.trigger.visible = false;
    if (state === 'inert') modal.trigger.inert = true;
    cleanup();
    assert.equal(modal.trigger.focused, 0);
    assert.deepEqual(env.overflow(), ['', '']);
  }
});

test('overlapping dialog effects retain scroll lock until the last cleanup, even out of order', () => {
  const env = modalLifecycleEnvironment('scroll', 'important');
  const first = env.session(), second = env.session();
  env.document.activeElement = first.trigger;
  const cleanupFirst = first.render(true, () => {})();
  const cleanupSecond = second.render(true, () => {})();
  cleanupFirst();
  assert.deepEqual(env.overflow(), ['hidden', '']);
  cleanupSecond();
  assert.deepEqual(env.overflow(), ['scroll', 'important']);
  assert.equal(first.listeners.size + second.listeners.size, 0);
});

test('mobile filter closes on the desktop breakpoint and removes its media listener on cleanup', () => {
  for (const initiallyDesktop of [false, true]) {
    const effects = [], changes = [], calls = [];
    let index = 0;
    const media = {
      matches: initiallyDesktop,
      addEventListener: (name, callback) => { assert.equal(name, 'change'); changes.push(callback); },
      removeEventListener: (name, callback) => { assert.equal(name, 'change'); assert.equal(changes.pop(), callback); },
    };
    const CatalogPage = loadSource('app/catalog/page.js', {
      react: {
        ...React,
        useState: (initial) => { const i = index++; return [i === 7 ? true : initial, (value) => calls.push([i, value])]; },
        useMemo: (compute) => compute(),
        useRef: (current) => ({ current }),
        useEffect: (setup) => effects.push(setup),
      },
      '@/context/CompareContext': { useCompare: () => ({ compareList: [] }) },
      '@/lib/useModalDialog': { useModalDialog: () => ({ dialogRef: {}, titleRef: {} }) },
      '@/lib/api': { getProducts: () => { throw new Error('Unexpected API request'); } },
    }, { window: { matchMedia: (query) => { assert.equal(query, '(min-width: 1024px)'); return media; } } }).default;
    CatalogPage();
    // Only exercise the breakpoint effect; the catalog API effect is not run.
    const cleanup = effects[0]();
    if (initiallyDesktop) assert.deepEqual(calls, [[7, false]]);
    else {
      assert.equal(calls.length, 0);
      media.matches = true;
      changes[0]();
      assert.deepEqual(calls, [[7, false]]);
    }
    cleanup();
    assert.equal(changes.length, 0);
  }
});

function reviewSurfaces(review) {
  const item = { ...product('sm-001'), review_sentiment: review };
  const { tree } = comparisonHarness().card(item);
  const card = findElements(tree, (node) => node.props.className?.includes('justify-between pt-2 border-t'))[0];
  const TabReviews = loadSource('components/product/TabReviews.js').default;
  return [card, TabReviews({ product: item })];
}

test('card and modal header label unchanged product prices as catalog prices regardless of product ID', () => {
  for (const id of ['sm-001', 'sm-003', 'lp-004']) {
    const item = product(id);
    const card = comparisonHarness().card(item).tree;
    const ProductModal = loadSource('components/product/ProductModal.js', {
      react: { ...React, useState: () => ['specs', () => {}] },
      '@/lib/api': { getLiveMarketplacePrices: () => { throw new Error('Unexpected API request'); } },
      '@/lib/useModalDialog': { useModalDialog: () => ({ dialogRef: {}, titleRef: {} }) },
      '@/context/CompareContext': { useCompare: () => ({ activeProductModal: item, isInCompare: () => false }) },
    }).default;
    for (const tree of [card, ProductModal()]) {
      assert.ok(textContent(tree).includes('Harga katalog'));
      assert.doesNotMatch(textContent(tree), /MSRP/);
      assert.equal(findElements(tree, (node) => Object.hasOwn(node.props, 'price'))[0].props.price, item.price);
    }
  }
});

test('supplied positive reviews keep their rating, count, summary and pros/cons without changing the dataset', () => {
  const snapshot = JSON.stringify(PRODUCTS);
  for (const item of PRODUCTS) {
    const review = item.review_sentiment;
    const [card, tab] = reviewSurfaces(review);
    for (const tree of [card, tab]) {
      assert.ok(findElements(tree, (node) => node.type === 'span' && node.props.children === review.overall_score).length);
      assert.doesNotMatch(textContent(tree), /Data ulasan belum tersedia/);
    }
    const compact = review.total_reviews > 999 ? (review.total_reviews / 1000).toFixed(1) + 'k' : review.total_reviews;
    assert.ok(textContent(card).includes(`(${compact} ulasan)`));
    assert.ok(textContent(tab).includes(review.total_reviews.toLocaleString('id-ID')));
    assert.ok(textContent(tab).includes(review.summary));
    for (const text of [...review.pros, ...review.cons]) assert.ok(textContent(tab).includes(text));
  }
  assert.equal(JSON.stringify(PRODUCTS), snapshot);
});

test('missing, null and zero-count reviews never invent rating or counts, including the backend default object', () => {
  const cases = [undefined, null, {}, { overall_score: 4.5, total_reviews: 0, pros: [], cons: [], summary: '' },
    { overall_score: 4.5 }, { overall_score: 4.5, total_reviews: null }];
  for (const review of cases) {
    for (const tree of reviewSurfaces(review)) {
      assert.ok(textContent(tree).includes('Data ulasan belum tersedia'));
      assert.doesNotMatch(textContent(tree), /4\.5|1k\+|1\.200\+|0 ulasan/);
      assert.equal(findElements(tree, (node) => node.type?.displayName === 'Star').length, 0);
      assert.doesNotMatch(renderToStaticMarkup(tree), /lucide-star/);
    }
  }
});

test('zero rating is preserved when a positive review count supports the aggregate', () => {
  for (const tree of reviewSurfaces({ overall_score: 0, total_reviews: 12 })) {
    assert.ok(findElements(tree, (node) => node.type === 'span' && node.props.children === 0).length);
    assert.ok(textContent(tree).includes('12'));
    assert.doesNotMatch(textContent(tree), /4\.5|Data ulasan belum tersedia/);
  }
});

test('partial or invalid numeric reviews display only supported fields', () => {
  for (const rating of [undefined, null, NaN, Infinity, -1, 6, '4.5']) {
    const [card, tab] = reviewSurfaces({ overall_score: rating, total_reviews: 12 });
    assert.ok(textContent(card).trim().startsWith('(12 ulasan)'));
    assert.ok(textContent(tab).includes('12 ulasan tercatat dalam data katalog.'));
    assert.ok(textContent(tab).includes('Rating belum tersedia'));
    for (const tree of [card, tab]) assert.doesNotMatch(renderToStaticMarkup(tree), /lucide-star/);
  }
  for (const count of [-1, 1.5, NaN, '12']) {
    for (const tree of reviewSurfaces({ overall_score: 4.2, total_reviews: count })) {
      assert.ok(textContent(tree).includes('Data ulasan belum tersedia'));
      assert.doesNotMatch(textContent(tree), /4\.2/);
    }
  }
});

test('partial review text renders safely without absent arrays or unsupported section placeholders', () => {
  const [, tab] = reviewSurfaces({ summary: 'Ringkasan tersedia', pros: ['Kelebihan tersedia', null, ' '], cons: null });
  assert.ok(textContent(tab).includes('Ringkasan tersedia'));
  assert.ok(textContent(tab).includes('Kelebihan tersedia'));
  assert.doesNotMatch(textContent(tab), /Kekurangan yang dicatat/);
  assert.equal(findElements(tab, (node) => node.type === 'li').length, 1);
  const [, consOnly] = reviewSurfaces({ cons: ['Kekurangan tersedia'], pros: {}, summary: null });
  assert.ok(textContent(consOnly).includes('Kekurangan tersedia'));
  assert.doesNotMatch(textContent(consOnly), /Ringkasan ulasan|Kelebihan yang dicatat/);
});

test('reviews do not claim verification, real-time provenance or a fixed sentiment distribution', () => {
  for (const review of [undefined, {}, product('sm-001').review_sentiment]) {
    const [, tab] = reviewSurfaces(review);
    assert.doesNotMatch(renderToStaticMarkup(tab), /Anti-Fake Verified|Real User Sentiment|ulasan nyata|Reddit|88%|12%/);
  }
});

test('dialog Tab boundaries wrap between operable controls while preserving normal and browser shortcuts', () => {
  const env = modalLifecycleEnvironment();
  const modal = env.session();
  const first = env.element(), middle = env.element(), last = env.element();
  const disabled = { ...env.element(), disabled: true };
  const hidden = { ...env.element(), visible: false };
  const inert = { ...env.element(), inert: true };
  const negative = { ...env.element(), tabIndex: -1 };
  const invisible = { ...env.element(), cssHidden: true };
  modal.dialog.controls = [disabled, hidden, first, middle, negative, last, inert, invisible];
  env.document.activeElement = modal.trigger;
  const cleanup = modal.render(true, () => {})();
  const keydown = modal.listeners.get('keydown');
  let prevented = 0;
  const tab = (extra = {}) => keydown({ key: 'Tab', preventDefault: () => prevented++, ...extra });
  last.focus();
  tab();
  assert.equal(env.document.activeElement, first);
  first.focus();
  tab({ shiftKey: true });
  assert.equal(env.document.activeElement, last);
  modal.title.focus();
  tab({ shiftKey: true });
  assert.equal(env.document.activeElement, last);
  assert.equal(prevented, 3);
  middle.focus();
  tab();
  assert.equal(env.document.activeElement, middle, 'Interior navigation remains native');
  last.focus();
  for (const modifier of ['ctrlKey', 'metaKey', 'altKey']) tab({ [modifier]: true });
  tab({ key: 'Enter' });
  assert.equal(prevented, 3);
  modal.dialog.controls = [];
  tab();
  assert.equal(env.document.activeElement, modal.title);
  assert.equal(prevented, 4);
  cleanup();
  assert.equal(modal.listeners.size, 0);
});
