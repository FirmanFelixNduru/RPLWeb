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
  const refs = [];
  let stateCursor = 0;
  let effectCursor = 0;
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
    useCallback(fn) {
      return fn;
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

describe('TabValue Product Identity & Lifecycle', () => {
  test('Scenario 1 — Render product with ID sm-001 triggers exactly one request', async () => {
    const requests = [];
    const mockGetPrices = async (id) => {
      requests.push(id);
      return { current_prices: [] };
    };

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1' },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {} },
    });

    // Wait for microtask tick
    await new Promise((resolve) => setTimeout(resolve, 10));
    h.rerender();

    assert.equal(requests.length, 1);
    assert.equal(requests[0], 'sm-001');
  });

  test('Scenario 2 — Re-rendering new object with same ID triggers no additional request', async () => {
    const requests = [];
    const mockGetPrices = async (id) => {
      requests.push(id);
      return { current_prices: [] };
    };

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1' },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {} },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));
    h.rerender();
    assert.equal(requests.length, 1);

    // New object reference with SAME id
    h.updateProps({ product: { id: 'sm-001', name: 'Phone 1 Renamed' } });
    await new Promise((resolve) => setTimeout(resolve, 10));
    h.rerender();

    assert.equal(requests.length, 1, 'Object reference change with same id must NOT trigger new request');
  });

  test('Scenario 3 — Changing ID to sm-002 triggers new request', async () => {
    const requests = [];
    const mockGetPrices = async (id) => {
      requests.push(id);
      return { current_prices: [] };
    };

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1' },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {} },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));
    h.rerender();
    assert.equal(requests.length, 1);

    // Change ID to sm-002
    h.updateProps({ product: { id: 'sm-002', name: 'Phone 2' } });
    await new Promise((resolve) => setTimeout(resolve, 10));
    h.rerender();

    assert.equal(requests.length, 2, 'Changing ID must trigger new request');
    assert.equal(requests[1], 'sm-002');
  });

  test('Scenario 4 — Slow request from old product does not overwrite state of new product', async () => {
    let resolveFirst;
    const firstPromise = new Promise((resolve) => { resolveFirst = resolve; });

    let resolveSecond;
    const secondPromise = new Promise((resolve) => { resolveSecond = resolve; });

    const mockGetPrices = (id) => {
      if (id === 'sm-001') return firstPromise;
      if (id === 'sm-002') return secondPromise;
      return Promise.resolve({ current_prices: [] });
    };

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1' },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {} },
    });

    // Change to sm-002 BEFORE sm-001 resolves
    h.updateProps({ product: { id: 'sm-002', name: 'Phone 2' } });

    // Now resolve sm-002 first
    resolveSecond({ current_prices: [{ marketplace: 'Store B', price: 2000 }] });
    await new Promise((resolve) => setTimeout(resolve, 10));
    h.rerender();

    assert.equal(h.getState(0)?.current_prices[0]?.price, 2000);

    // Now resolve sm-001 late
    resolveFirst({ current_prices: [{ marketplace: 'Store A', price: 1000 }] });
    await new Promise((resolve) => setTimeout(resolve, 10));
    h.rerender();

    // Verify sm-001 response did not overwrite sm-002
    assert.equal(h.getState(0)?.current_prices[0]?.price, 2000, 'Late old response must not overwrite current product');
  });

  test('Scenario 5 — Component unmount before request finishes prevents state update', async () => {
    let resolveRequest;
    const promise = new Promise((resolve) => { resolveRequest = resolve; });
    const mockGetPrices = () => promise;

    const h = createHarness('components/product/TabValue', {
      product: { id: 'sm-001', name: 'Phone 1' },
    }, {
      '@/lib/api': { getLiveMarketplacePrices: mockGetPrices },
    }, {
      console: { error: () => {} },
    });

    // Unmount before resolving
    h.unmount();

    // Resolving after unmount
    resolveRequest({ current_prices: [{ price: 999 }] });
    await new Promise((resolve) => setTimeout(resolve, 10));

    assert.equal(h.getState(0), null, 'Unmounted component must not update pricingData');
  });
});
