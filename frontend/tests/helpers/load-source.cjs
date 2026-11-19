const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { transformSync } = require('next/dist/build/swc');

module.exports = function loadSource(entry, overrides = {}, globals = {}) {
  const root = path.resolve(__dirname, '../../src');
  const cache = new Map();
  function load(filename) {
    if (cache.has(filename)) return cache.get(filename).exports;
    const mod = { exports: {} };
    cache.set(filename, mod);
    const { code } = transformSync(fs.readFileSync(filename, 'utf8'), {
      filename,
      jsc: { parser: { syntax: 'ecmascript', jsx: true }, transform: { react: { runtime: 'classic' } } },
      module: { type: 'commonjs' },
    });
    const localRequire = name => {
      if (Object.hasOwn(overrides, name)) return overrides[name];
      if (name.startsWith('@/')) return load(path.join(root, `${name.slice(2)}.js`));
      if (name.startsWith('.')) return load(path.resolve(path.dirname(filename), `${name}.js`));
      return require(name);
    };
    vm.runInNewContext(`(function(require,module,exports){${code}\n})`, globals)(localRequire, mod, mod.exports);
    return mod.exports;
  }
  return load(path.join(root, entry));
};
