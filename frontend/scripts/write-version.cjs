const fs = require('node:fs');
const { execFileSync } = require('node:child_process');
const path = require('node:path');
function git(...args) {
  try { return execFileSync('git', args, { encoding: 'utf8' }).trim(); }
  catch { return 'unknown'; }
}
const version = { version: require('../package.json').version,
  commit: process.env.GITHUB_SHA || git('rev-parse', 'HEAD'),
  branch: process.env.GITHUB_REF_NAME || git('branch', '--show-current'),
  builtAt: new Date().toISOString() };
fs.writeFileSync(path.resolve(__dirname, '../public/version.json'), JSON.stringify(version, null, 2));
