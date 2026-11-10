const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test, describe } = require('node:test');
const React = require('react');
const { transformSync } = require('next/dist/build/swc');

const sourceRoot = path.resolve(__dirname, '../src');

function loadSource(entry, overrides = {}, globals = {}) {
  const cache = new Map();
  function load(filename) {
    if (cache.has(filename)) return cache.get(filename).exports;
    const mod = { exports: {} };
    cache.set(filename, mod);
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
    evaluate(requireSource, mod, mod.exports);
    return mod.exports;
  }
  const resolvedEntry = entry.endsWith('.js') ? entry : `${entry}.js`;
  return load(path.join(sourceRoot, resolvedEntry));
}

function createScheduler() {
  const queue = [];
  return {
    queueMicrotask: (cb) => { queue.push(cb); },
    flush: () => {
      let count = 0;
      while (queue.length > 0) {
        const cb = queue.shift();
        cb();
        count++;
      }
      return count;
    },
    get size() { return queue.length; },
    clear: () => { queue.length = 0; },
  };
}

function createHarness(ComponentPath, initialProps = {}, overrides = {}, globals = {}, initialStates = {}, filterEffects = () => true) {
  const states = [];
  const stateSetters = [];
  const effects = [];
  const callbacks = [];
  const refs = [];
  let stateCursor = 0;
  let effectCursor = 0;
  let callbackCursor = 0;
  let refCursor = 0;
  let currentProps = { ...initialProps };
  let dirty = false;
  let tree = null;

  const mockReact = {
    ...React,
    useState(initial) {
      const idx = stateCursor++;
      if (states.length <= idx) {
        if (Object.hasOwn(initialStates, idx)) {
          states[idx] = initialStates[idx];
        } else {
          states[idx] = typeof initial === 'function' ? initial() : initial;
        }
        stateSetters[idx] = (action) => {
          const next = typeof action === 'function' ? action(states[idx]) : action;
          if (!Object.is(states[idx], next)) {
            states[idx] = next;
            dirty = true;
          }
        };
      }
      return [states[idx], stateSetters[idx]];
    },
    useRef(initial) {
      const idx = refCursor++;
      if (refs.length <= idx) {
        refs[idx] = { current: initial };
      }
      return refs[idx];
    },
    useMemo(fn) {
      return fn();
    },
    useCallback(fn, deps) {
      const idx = callbackCursor++;
      const prev = callbacks[idx];
      const hasChanged = !prev || !deps || deps.some((d, i) => !Object.is(d, prev.deps[i]));
      if (hasChanged) {
        callbacks[idx] = { fn, deps };
        return fn;
      }
      return prev.fn;
    },
    useEffect(setup, deps) {
      const idx = effectCursor++;
      const prev = effects[idx];
      const hasChanged = !prev || !deps || deps.some((d, i) => !Object.is(d, prev.deps[i]));
      if (hasChanged) {
        effects[idx] = {
          setup,
          deps,
          cleanup: prev?.cleanup,
          pending: true,
        };
      }
    },
    useContext(ctx) {
      return ctx._currentValue || {};
    },
  };

  const loaded = loadSource(ComponentPath, {
    react: mockReact,
    ...overrides,
  }, globals);

  const Component = loaded.default || loaded.ThemeProvider || loaded.CompareProvider || loaded;

  function render() {
    let iterations = 0;
    do {
      dirty = false;
      stateCursor = 0;
      effectCursor = 0;
      callbackCursor = 0;
      refCursor = 0;
      tree = Component(currentProps);
      iterations++;
      if (iterations > 25) throw new Error('Excessive re-renders in harness');
    } while (dirty);

    for (let i = 0; i < effects.length; i++) {
      const eff = effects[i];
      if (eff.pending && filterEffects(i)) {
        eff.cleanup?.();
        eff.pending = false;
        eff.cleanup = eff.setup?.();
      }
    }
  }

  render();

  return {
    get tree() { return tree; },
    get states() { return states; },
    get refs() { return refs; },
    updateProps(newProps) {
      currentProps = { ...currentProps, ...newProps };
      render();
    },
    rerender() {
      render();
    },
    unmount() {
      for (const eff of effects) {
        eff.cleanup?.();
        eff.cleanup = null;
      }
    },
    strictModeRemount() {
      for (let i = 0; i < effects.length; i++) {
        const eff = effects[i];
        if (filterEffects(i)) {
          eff.cleanup?.();
          eff.cleanup = null;
          eff.pending = true;
        }
      }
      render();
    },
    getState(idx) {
      return states[idx];
    },
    setState(idx, val) {
      stateSetters[idx]?.(val);
      render();
    },
  };
}

describe('ThemeContext Microtask Lifecycle', () => {
  function makeEnv() {
    const scheduler = createScheduler();
    const classList = new Set(['dark']);
    const store = new Map();
    const documentMock = {
      documentElement: {
        classList: {
          add: (cls) => classList.add(cls),
          remove: (cls) => classList.delete(cls),
          contains: (cls) => classList.has(cls),
        },
      },
    };
    const localStorageMock = {
      getItem: (k) => store.get(k) || null,
      setItem: (k, v) => store.set(k, String(v)),
      removeItem: (k) => store.delete(k),
    };
    const windowMock = {
      matchMedia: () => ({ matches: false }), // prefers light by default
    };
    return { scheduler, classList, store, documentMock, localStorageMock, windowMock };
  }

  test('Test A — Normal execution: queues microtask and applies theme after flush', () => {
    const env = makeEnv();
    env.store.set('comparebuy_theme', 'light');

    const h = createHarness('context/ThemeContext', { children: null }, {}, {
      document: env.documentMock,
      localStorage: env.localStorageMock,
      window: env.windowMock,
      queueMicrotask: env.scheduler.queueMicrotask,
    });

    assert.equal(env.scheduler.size, 1, 'Microtask must be queued, not executed synchronously');
    assert.equal(h.getState(1), false, 'mounted should be false initially');

    const flushed = env.scheduler.flush();
    assert.equal(flushed, 1);
    h.rerender();

    assert.equal(h.getState(0), 'light', 'theme should be hydrated to light');
    assert.equal(h.getState(1), true, 'mounted should be true after flush');
    assert.ok(!env.classList.has('dark'), 'document dark class should be removed');
  });

  test('Test B — Cleanup before flush: unmounting cancels microtask state mutation', () => {
    const env = makeEnv();
    env.store.set('comparebuy_theme', 'light');

    const h = createHarness('context/ThemeContext', { children: null }, {}, {
      document: env.documentMock,
      localStorage: env.localStorageMock,
      window: env.windowMock,
      queueMicrotask: env.scheduler.queueMicrotask,
    });

    assert.equal(env.scheduler.size, 1);
    h.unmount(); // cleanup runs before microtask flushes

    env.scheduler.flush();
    h.rerender();

    assert.equal(h.getState(0), 'dark', 'cancelled callback must not update theme');
    assert.equal(h.getState(1), false, 'cancelled callback must not set mounted to true');
    assert.ok(env.classList.has('dark'), 'cancelled callback must not alter DOM classList');
  });

  test('Test C — Strict Mode-like lifecycle: setup -> cleanup -> setup flushes safely', () => {
    const env = makeEnv();
    env.store.set('comparebuy_theme', 'light');

    const h = createHarness('context/ThemeContext', { children: null }, {}, {
      document: env.documentMock,
      localStorage: env.localStorageMock,
      window: env.windowMock,
      queueMicrotask: env.scheduler.queueMicrotask,
    });

    assert.equal(env.scheduler.size, 1);
    h.strictModeRemount(); // cleans up first effect, schedules second
    assert.equal(env.scheduler.size, 2);

    env.scheduler.flush();
    h.rerender();

    assert.equal(h.getState(0), 'light', 'active setup correctly sets theme');
    assert.equal(h.getState(1), true, 'mounted state is true');
    assert.ok(!env.classList.has('dark'));
  });

  test('Test D — Rapid preference changes: fallback to system preference when storage empty', () => {
    const env = makeEnv();
    // No saved theme, system prefers light
    const h = createHarness('context/ThemeContext', { children: null }, {}, {
      document: env.documentMock,
      localStorage: env.localStorageMock,
      window: env.windowMock,
      queueMicrotask: env.scheduler.queueMicrotask,
    });

    env.scheduler.flush();
    h.rerender();

    assert.equal(h.getState(0), 'light');
    assert.equal(h.getState(1), true);
  });
});

describe('CompareContext Microtask Lifecycle', () => {
  function makeEnv() {
    const scheduler = createScheduler();
    const store = new Map();
    const localStorageMock = {
      getItem: (k) => store.get(k) || null,
      setItem: (k, v) => store.set(k, String(v)),
      removeItem: (k) => store.delete(k),
    };
    return { scheduler, store, localStorageMock };
  }

  test('Test A — Normal execution: hydrates dock from localStorage upon flush', () => {
    const env = makeEnv();
    env.store.set('comparebuy_dock', JSON.stringify([{ id: 'sm-001', name: 'Test 1' }]));

    const h = createHarness('context/CompareContext', { children: null }, {}, {
      localStorage: env.localStorageMock,
      queueMicrotask: env.scheduler.queueMicrotask,
      console: { warn: () => {} },
    });

    assert.equal(env.scheduler.size, 1);
    assert.equal(h.getState(0).length, 0, 'compareList initially empty');

    env.scheduler.flush();
    h.rerender();

    assert.equal(h.getState(0).length, 1);
    assert.equal(h.getState(0)[0].id, 'sm-001');
  });

  test('Test B — Cleanup before flush: unmount cancels dock hydration callback', () => {
    const env = makeEnv();
    env.store.set('comparebuy_dock', JSON.stringify([{ id: 'sm-001', name: 'Test 1' }]));

    const h = createHarness('context/CompareContext', { children: null }, {}, {
      localStorage: env.localStorageMock,
      queueMicrotask: env.scheduler.queueMicrotask,
      console: { warn: () => {} },
    });

    assert.equal(env.scheduler.size, 1);
    h.unmount();

    env.scheduler.flush();
    h.rerender();

    assert.equal(h.getState(0).length, 0, 'cancelled callback must not hydrate compareList');
  });

  test('Test C — Strict Mode: setup-cleanup-setup only hydrates from active effect', () => {
    const env = makeEnv();
    env.store.set('comparebuy_dock', JSON.stringify([{ id: 'lp-001', name: 'Laptop 1' }]));

    const h = createHarness('context/CompareContext', { children: null }, {}, {
      localStorage: env.localStorageMock,
      queueMicrotask: env.scheduler.queueMicrotask,
      console: { warn: () => {} },
    });

    h.strictModeRemount();
    assert.equal(env.scheduler.size, 2);

    env.scheduler.flush();
    h.rerender();

    assert.equal(h.getState(0).length, 1);
    assert.equal(h.getState(0)[0].id, 'lp-001');
  });
});

describe('Catalog Page Status Host & Announcement Lifecycle', () => {
  function makeCatalogHarness(initialProps = {}, customOverrides = {}) {
    const scheduler = createScheduler();
    const timers = new Map();
    let time = 0;
    let timerId = 0;
    const hosts = [];
    const containerMock = () => ({
      children: [],
      appendChild(node) {
        node.remove?.();
        this.children.push(node);
        node.parentNode = this;
      },
    });

    const home = containerMock();
    const searchContainerRef = { current: home };
    const filterDialogRef = { current: containerMock() };

    const documentMock = {
      createElement: (tag) => {
        const node = {
          tag,
          attributes: {},
          textContent: '',
          parentNode: null,
          setAttribute(k, v) { this.attributes[k] = v; },
          remove() {
            if (this.parentNode) {
              const idx = this.parentNode.children.indexOf(this);
              if (idx !== -1) this.parentNode.children.splice(idx, 1);
            }
            this.parentNode = null;
          },
        };
        hosts.push(node);
        return node;
      },
    };

    const globals = {
      document: documentMock,
      setTimeout: (cb, delay) => {
        const id = ++timerId;
        timers.set(id, { cb, due: time + delay });
        return id;
      },
      clearTimeout: (id) => timers.delete(id),
      queueMicrotask: scheduler.queueMicrotask,
    };

    const overrides = {
      'react-dom': {
        createPortal: (msg, host) => {
          if (host) host.textContent = msg;
          return null;
        },
      },
      '@/context/CompareContext': { useCompare: () => ({ compareList: [] }) },
      '@/lib/useModalDialog': { useModalDialog: () => ({ dialogRef: filterDialogRef, titleRef: {} }) },
      '@/lib/api': { getProducts: () => Promise.resolve({ products: [] }) },
      ...customOverrides,
    };

    const h = createHarness(
      'app/catalog/page',
      initialProps,
      overrides,
      globals,
      { 0: [{ id: 'p1' }], 1: false },
      (idx) => idx >= 2
    );
    if (h.refs[0]) h.refs[0].current = home;

    return {
      harness: h,
      home,
      scheduler,
      timers,
      hosts,
      advance: (ms) => {
        time += ms;
        for (const [id, timer] of [...timers]) {
          if (timer.due <= time) {
            timers.delete(id);
            timer.cb();
          }
        }
        h.rerender();
      },
      unmount: () => h.unmount(),
    };
  }

  test('Test A — Status host normal execution: microtask sets statusHost and appends to DOM', () => {
    const { harness, scheduler, hosts, home } = makeCatalogHarness();
    assert.ok(scheduler.size >= 1, 'Status host setup queues a microtask');

    scheduler.flush();
    if (harness.refs[0]) harness.refs[0].current = home;
    harness.rerender();

    assert.equal(hosts.length, 1);
    assert.equal(hosts[0].attributes.role, 'status');
    assert.ok(hosts[0].parentNode !== null, 'host should be attached to parent node');
  });

  test('Test B — Status host cleanup before flush: unmount removes host and prevents state set', () => {
    const { harness, scheduler, hosts, unmount } = makeCatalogHarness();
    assert.ok(scheduler.size >= 1);

    unmount(); // Unmount before microtask runs
    scheduler.flush();
    harness.rerender();

    assert.equal(hosts.length, 1);
    assert.equal(hosts[0].parentNode, null, 'Unmounted host must not remain in DOM');
  });

  test('Test C — Strict Mode: setup -> cleanup -> setup sets host once without orphan node', () => {
    const { harness, scheduler, hosts, home } = makeCatalogHarness();
    harness.strictModeRemount();

    scheduler.flush();
    if (harness.refs[0]) harness.refs[0].current = home;
    harness.rerender();

    const attached = hosts.filter((h) => h.parentNode !== null);
    assert.equal(attached.length, 1, 'Exactly one status host must be attached');
  });

  test('Test D & E — Result announcement lifecycle: timer cancelled on cleanup without stale announcement', () => {
    const { harness, scheduler, timers, advance, unmount, hosts } = makeCatalogHarness();
    scheduler.flush();
    harness.rerender();

    assert.equal(timers.size, 1, 'Timer for announcement should be scheduled when loading is false');
    unmount();

    assert.equal(timers.size, 0, 'Unmount must clear announcement timer');
    assert.equal(hosts[0].parentNode, null, 'Unmount must remove host');
  });
});

function createDeferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

async function flushMicrotasks() {
  for (let i = 0; i < 6; i++) {
    await Promise.resolve();
  }
}

function findRefreshButton(tree) {
  if (!tree || typeof tree !== 'object') return null;
  if (tree.type === 'button') {
    const props = tree.props || {};
    const text = JSON.stringify(props.children);
    if (text && (text.includes('Perbarui') || text.includes('Memperbarui') || text.includes('RefreshCw'))) {
      return tree;
    }
  }
  const children = Array.isArray(tree.props?.children)
    ? tree.props.children
    : [tree.props?.children];
  for (const child of children) {
    const found = findRefreshButton(child);
    if (found) return found;
  }
  return null;
}

describe('TabValue Product Identity & Lifecycle', () => {
  test('Test 1 — Normal manual refresh: click refresh sets refreshing=true, resolves, updates data, sets refreshing=false', async () => {
    const initialDef = createDeferred();
    const refreshDef = createDeferred();
    let callCount = 0;
    const requests = [];

    const mockGetPrices = async (id) => {
      requests.push(id);
      callCount++;
      return callCount === 1 ? initialDef.promise : refreshDef.promise;
    };

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1', price: 5000000 },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {}, log: () => {} },
    });

    assert.equal(requests.length, 1);
    assert.equal(h.getState(1), true, 'loading should be true initially');
    assert.equal(h.getState(2), false, 'refreshing should be false initially');

    // 2. Resolve initial request
    initialDef.resolve({
      prices: [{ marketplace: 'Shopee', price: 4900000, source: 'scraped' }],
      last_updated: 'Just now',
    });
    await flushMicrotasks();
    h.rerender();

    assert.equal(h.getState(1), false, 'loading should be false after initial resolution');
    assert.equal(h.getState(2), false, 'refreshing should still be false');
    assert.equal(h.getState(0)?.prices[0]?.price, 4900000, 'initial pricing data should be set');

    // 3. Trigger manual refresh
    const btn = findRefreshButton(h.tree);
    assert.ok(btn, 'Refresh button must be rendered');
    btn.props.onClick();
    h.rerender();

    // 4. Verify refreshing=true
    assert.equal(requests.length, 2, 'manual refresh should trigger second request');
    assert.equal(h.getState(2), true, 'refreshing should be true while refresh is pending');
    assert.equal(h.getState(1), false, 'loading should remain false during manual refresh');

    // 5. Resolve refresh request
    refreshDef.resolve({
      prices: [{ marketplace: 'Shopee', price: 4750000, source: 'scraped' }],
      last_updated: 'Updated recently',
    });
    await flushMicrotasks();
    h.rerender();

    // 6. Verify updated price and 7. refreshing=false
    assert.equal(h.getState(0)?.prices[0]?.price, 4750000, 'pricing data must reflect refreshed price');
    assert.equal(h.getState(2), false, 'refreshing should be false after refresh completes');
    assert.equal(h.getState(1), false, 'loading should remain false');
  });

  test('Test 2 — Old refresh cannot overwrite new product: delayed sm-001 refresh cannot overwrite sm-002', async () => {
    const initialDef1 = createDeferred();
    const refreshDef1 = createDeferred();
    const initialDef2 = createDeferred();
    const requests = [];

    const mockGetPrices = async (id) => {
      requests.push(id);
      if (id === 'sm-001') {
        return requests.filter((r) => r === 'sm-001').length === 1
          ? initialDef1.promise
          : refreshDef1.promise;
      }
      return initialDef2.promise;
    };

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1', price: 5000000 },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {}, log: () => {} },
    });

    // Resolve initial request for sm-001
    initialDef1.resolve({
      prices: [{ marketplace: 'Shopee', price: 5000000, source: 'scraped' }],
    });
    await flushMicrotasks();
    h.rerender();
    assert.equal(h.getState(0)?.prices[0]?.price, 5000000);

    // Start manual refresh on sm-001
    const btn = findRefreshButton(h.tree);
    btn.props.onClick();
    h.rerender();
    assert.equal(h.getState(2), true, 'refreshing should be true');

    // Switch product to sm-002 before sm-001 refresh resolves
    h.updateProps({ product: { id: 'sm-002', name: 'Phone 2', price: 7000000 } });
    assert.equal(h.getState(1), true, 'loading should be true for sm-002');
    assert.equal(h.getState(2), false, 'refreshing should be reset to false for sm-002');
    assert.equal(h.getState(0), null, 'pricingData should be reset to null for sm-002');

    // Resolve initial request for sm-002
    initialDef2.resolve({
      prices: [{ marketplace: 'Tokopedia', price: 6800000, source: 'scraped' }],
    });
    await flushMicrotasks();
    h.rerender();
    assert.equal(h.getState(0)?.prices[0]?.price, 6800000, 'sm-002 prices loaded');
    assert.equal(h.getState(1), false, 'loading false for sm-002');

    // Now resolve old sm-001 refresh late
    refreshDef1.resolve({
      prices: [{ marketplace: 'Shopee', price: 4200000, source: 'scraped' }],
    });
    await flushMicrotasks();
    h.rerender();

    // Verify sm-002 data is untouched by sm-001 refresh
    assert.equal(h.getState(0)?.prices[0]?.price, 6800000, 'stale refresh must not overwrite new product data');
    assert.equal(h.getState(1), false, 'loading must stay false');
    assert.equal(h.getState(2), false, 'refreshing must stay false');
  });

  test('Test 3 — Old refresh finally cannot clear new loading state: old refresh resolution leaves new product loading=true', async () => {
    const initialDef1 = createDeferred();
    const refreshDef1 = createDeferred();
    const initialDef2 = createDeferred();
    const requests = [];

    const mockGetPrices = async (id) => {
      requests.push(id);
      if (id === 'sm-001') {
        return requests.filter((r) => r === 'sm-001').length === 1
          ? initialDef1.promise
          : refreshDef1.promise;
      }
      return initialDef2.promise;
    };

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1', price: 5000000 },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {}, log: () => {} },
    });

    initialDef1.resolve({ prices: [{ marketplace: 'Shopee', price: 5000000, source: 'scraped' }] });
    await flushMicrotasks();
    h.rerender();

    // Start manual refresh on sm-001
    const btn = findRefreshButton(h.tree);
    btn.props.onClick();
    h.rerender();
    assert.equal(h.getState(2), true);

    // Switch to sm-002 while sm-002 initial is still pending
    h.updateProps({ product: { id: 'sm-002', name: 'Phone 2', price: 8000000 } });
    assert.equal(h.getState(1), true, 'sm-002 is loading');
    assert.equal(h.getState(2), false, 'refreshing is false');

    // Resolve old sm-001 refresh while sm-002 is still waiting
    refreshDef1.resolve({ prices: [{ marketplace: 'Shopee', price: 4000000, source: 'scraped' }] });
    await flushMicrotasks();
    h.rerender();

    // Must NOT clear sm-002 loading state or set sm-001 data
    assert.equal(h.getState(1), true, 'loading state of new product must NOT be cleared by old refresh');
    assert.equal(h.getState(2), false, 'refreshing state must stay false');
    assert.equal(h.getState(0), null, 'pricingData must remain null while sm-002 is pending');

    // Finally resolve sm-002 initial request
    initialDef2.resolve({ prices: [{ marketplace: 'Tokopedia', price: 7900000, source: 'scraped' }] });
    await flushMicrotasks();
    h.rerender();

    assert.equal(h.getState(0)?.prices[0]?.price, 7900000, 'sm-002 final price should be correct');
    assert.equal(h.getState(1), false, 'loading should now be false');
    assert.equal(h.getState(2), false, 'refreshing should be false');
  });

  test('Test 4 — Refresh supersedes initial request: delayed initial request cannot overwrite newer refresh result', async () => {
    const initialDef = createDeferred();
    const refreshDef = createDeferred();
    let count = 0;

    const mockGetPrices = async () => {
      count++;
      return count === 1 ? initialDef.promise : refreshDef.promise;
    };

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1', price: 5000000 },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {}, log: () => {} },
    });

    assert.equal(h.getState(1), true, 'initial request is loading');

    // User triggers manual refresh before initial request resolves
    const btn = findRefreshButton(h.tree);
    btn.props.onClick();
    h.rerender();
    assert.equal(h.getState(2), true, 'refreshing is true');

    // Resolve refresh request FIRST with newer data (price 4500000)
    refreshDef.resolve({
      prices: [{ marketplace: 'Shopee', price: 4500000, source: 'scraped' }],
    });
    await flushMicrotasks();
    h.rerender();

    assert.equal(h.getState(0)?.prices[0]?.price, 4500000, 'pricingData updated with refreshed price');
    assert.equal(h.getState(2), false, 'refreshing should be false');
    assert.equal(h.getState(1), false, 'loading should be false');

    // Resolve initial request LATER with older data (price 5000000)
    initialDef.resolve({
      prices: [{ marketplace: 'Shopee', price: 5000000, source: 'scraped' }],
    });
    await flushMicrotasks();
    h.rerender();

    // Verify older initial request was discarded and did not overwrite the newer refresh
    assert.equal(h.getState(0)?.prices[0]?.price, 4500000, 'superseded initial request must not overwrite newer refresh');
  });

  test('Test 5 — Old refresh rejection: rejection of stale refresh does not affect new product state', async () => {
    const initialDef1 = createDeferred();
    const refreshDef1 = createDeferred();
    const initialDef2 = createDeferred();
    const requests = [];

    const mockGetPrices = async (id) => {
      requests.push(id);
      if (id === 'sm-001') {
        return requests.filter((r) => r === 'sm-001').length === 1
          ? initialDef1.promise
          : refreshDef1.promise;
      }
      return initialDef2.promise;
    };

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1', price: 5000000 },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {}, log: () => {} },
    });

    initialDef1.resolve({ prices: [{ marketplace: 'Shopee', price: 5000000, source: 'scraped' }] });
    await flushMicrotasks();
    h.rerender();

    // Start manual refresh on sm-001
    const btn = findRefreshButton(h.tree);
    btn.props.onClick();
    h.rerender();

    // Switch to sm-002
    h.updateProps({ product: { id: 'sm-002', name: 'Phone 2', price: 9000000 } });
    assert.equal(h.getState(1), true, 'sm-002 is loading');

    // Reject old sm-001 refresh
    refreshDef1.reject(new Error('Network failure on sm-001 refresh'));
    await flushMicrotasks();
    h.rerender();

    // Verify sm-002 state unaffected
    assert.equal(h.getState(1), true, 'sm-002 loading must stay true despite old refresh rejection');
    assert.equal(h.getState(2), false, 'sm-002 refreshing must stay false');
    assert.equal(h.getState(0), null, 'sm-002 pricingData must stay null');

    // Resolve sm-002 initial normally
    initialDef2.resolve({ prices: [{ marketplace: 'Lazada', price: 8800000, source: 'scraped' }] });
    await flushMicrotasks();
    h.rerender();

    assert.equal(h.getState(0)?.prices[0]?.price, 8800000, 'sm-002 should resolve normally');
    assert.equal(h.getState(1), false);
    assert.equal(h.getState(2), false);
  });

  test('Test 6 — Unmount during manual refresh: resolution after unmount does not mutate state', async () => {
    const initialDef = createDeferred();
    const refreshDef = createDeferred();
    let count = 0;

    const mockGetPrices = async () => {
      count++;
      return count === 1 ? initialDef.promise : refreshDef.promise;
    };

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1', price: 5000000 },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {}, log: () => {} },
    });

    initialDef.resolve({
      prices: [{ marketplace: 'Shopee', price: 5000000, source: 'scraped' }],
    });
    await flushMicrotasks();
    h.rerender();
    assert.equal(h.getState(0)?.prices[0]?.price, 5000000);

    // Start manual refresh
    const btn = findRefreshButton(h.tree);
    btn.props.onClick();
    h.rerender();
    assert.equal(h.getState(2), true, 'refreshing is true');

    // Unmount component while refresh is pending
    h.unmount();

    // Resolve refresh after unmount
    refreshDef.resolve({
      prices: [{ marketplace: 'Shopee', price: 4200000, source: 'scraped' }],
    });
    await flushMicrotasks();

    // Verify state was not mutated by the completed promise after unmount
    assert.equal(h.getState(0)?.prices[0]?.price, 5000000, 'pricingData must not be mutated after unmount');
  });

  test('Test 7 — Same ID, new object reference: re-rendering with new object reference triggers no additional request', async () => {
    const requests = [];
    const def = createDeferred();
    const mockGetPrices = async (id) => {
      requests.push(id);
      return def.promise;
    };

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1' },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {} },
    });

    def.resolve({ current_prices: [] });
    await flushMicrotasks();
    h.rerender();
    assert.equal(requests.length, 1);

    // New object reference with SAME id
    h.updateProps({ product: { id: 'sm-001', name: 'Phone 1 Renamed' } });
    await flushMicrotasks();
    h.rerender();

    assert.equal(requests.length, 1, 'Object reference change with same id must NOT trigger new request');
  });

  test('Test 8 — New product ID: changing ID triggers new request and old response cannot overwrite', async () => {
    const requests = [];
    const def1 = createDeferred();
    const def2 = createDeferred();

    const mockGetPrices = async (id) => {
      requests.push(id);
      return id === 'sm-001' ? def1.promise : def2.promise;
    };

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1' },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {} },
    });

    assert.equal(requests.length, 1);
    assert.equal(requests[0], 'sm-001');

    // Change ID to sm-002 before sm-001 resolves
    h.updateProps({ product: { id: 'sm-002', name: 'Phone 2' } });
    assert.equal(requests.length, 2, 'Changing ID must trigger new request');
    assert.equal(requests[1], 'sm-002');

    // Resolve sm-002 first
    def2.resolve({ current_prices: [{ marketplace: 'Store B', price: 2000 }] });
    await flushMicrotasks();
    h.rerender();
    assert.equal(h.getState(0)?.current_prices[0]?.price, 2000);

    // Resolve sm-001 late
    def1.resolve({ current_prices: [{ marketplace: 'Store A', price: 1000 }] });
    await flushMicrotasks();
    h.rerender();

    assert.equal(h.getState(0)?.current_prices[0]?.price, 2000, 'Late old response must not overwrite current product');
  });

  test('Scenario 1 (Baseline) — Render product with ID sm-001 triggers exactly one request', async () => {
    const requests = [];
    const def = createDeferred();
    const mockGetPrices = async (id) => {
      requests.push(id);
      return def.promise;
    };

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1' },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {} },
    });

    def.resolve({ current_prices: [] });
    await flushMicrotasks();
    h.rerender();

    assert.equal(requests.length, 1);
    assert.equal(requests[0], 'sm-001');
  });

  test('Scenario 5 (Baseline) — Component unmount before initial request finishes prevents state update', async () => {
    const def = createDeferred();
    const mockGetPrices = () => def.promise;

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1' },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {} },
    });

    h.unmount();

    def.resolve({ current_prices: [{ price: 999 }] });
    await flushMicrotasks();

    assert.equal(h.getState(0), null, 'Unmounted component must not update pricingData');
  });
});
