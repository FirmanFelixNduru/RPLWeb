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
    },
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
  detail.props.onClick();
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

test('product name is a noninteractive heading while detail remains a keyboard-native button', () => {
  const harness = comparisonHarness();
  const { tree } = harness.card(product('sm-001'));
  const heading = findElements(tree, (node) => node.type === 'h3')[0];
  assert.equal(heading.props.onClick, undefined);
  assert.equal(heading.props.tabIndex, undefined);
  const detail = findElements(tree, (node) => node.type === 'button' && textContent(node) === 'Lihat Detail')[0];
  assert.equal(detail.props.type, 'button');
  detail.props.onClick();
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
  const metadata = findElements(card, (node) => node.type === 'span' && textContent(node) === 'MSRP')[0];
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
