const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const reportDir = path.resolve(__dirname, '../reports');
const root = path.resolve(__dirname, '..');
fs.mkdirSync(reportDir, { recursive: true });
const startedAt = new Date().toISOString();
const minimum = 200;
const writeSummary = data => fs.writeFileSync(path.join(reportDir, 'summary.json'), JSON.stringify(data, null, 2));
writeSummary({ status: 'running', startedAt, minimum, commit: process.env.GITHUB_SHA || null });
const files = fs.readdirSync(path.join(root, 'tests')).filter(name => name.endsWith('.test.cjs')).sort().map(name => `tests/${name}`);
const child = spawn(process.execPath, ['--test', '--test-reporter=tap', '--test-reporter-destination=stdout',
  '--test-reporter=junit', `--test-reporter-destination=${path.join(reportDir, 'junit.xml')}`, ...files], { cwd: root });
let output = '';
child.stdout.on('data', chunk => { output += chunk; process.stdout.write(chunk); });
child.stderr.on('data', chunk => process.stderr.write(chunk));
child.on('error', error => {
  writeSummary({ status: 'failed', startedAt, error: error.message, minimum });
  process.exitCode = 1;
});
child.on('close', code => {
  fs.writeFileSync(path.join(reportDir, 'unit-tests.tap'), output);
  const count = key => Number(output.match(new RegExp(`^# ${key} (\\d+)$`, 'm'))?.[1] || 0);
  const summary = { status: 'failed', startedAt, finishedAt: new Date().toISOString(),
    commit: process.env.GITHUB_SHA || null, minimum,
    tests: count('tests'), passed: count('pass'), failed: count('fail'), skipped: count('skipped'), todo: count('todo'), cancelled: count('cancelled'), exitCode: code };
  const passed = code === 0 && summary.tests >= minimum && summary.passed === summary.tests &&
    summary.failed === 0 && summary.skipped === 0 && summary.todo === 0 && summary.cancelled === 0;
  summary.status = passed ? 'passed' : 'failed';
  writeSummary(summary);
  console.log(`\nP11 gate: ${summary.tests} tests; ${summary.passed} passed; ${summary.failed} failed; ${summary.skipped} skipped. ${passed ? 'PASS' : 'BLOCK BUILD/DEPLOY'}`);
  process.exitCode = passed ? 0 : 1;
});
