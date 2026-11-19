const fs = require('node:fs');
const path = require('node:path');
const base = process.env.DEPLOYMENT_URL?.replace(/\/$/, '');
const expectedCommit = process.env.GITHUB_SHA;
if (!base || !expectedCommit) throw Error('DEPLOYMENT_URL and GITHUB_SHA are required');
const report = { testedAt: new Date().toISOString(), url: base, expectedCommit, checks: [] };
(async () => {
  try {
    for (const route of ['/version.json', '/', '/catalog', '/wizard', '/compare']) {
      const response = await fetch(base + route, { signal: AbortSignal.timeout(30000) });
      const check = { route, status: response.status, passed: response.ok };
      if (route === '/version.json' && response.ok) {
        check.version = await response.json();
        check.passed = check.version.commit === expectedCommit;
      }
      report.checks.push(check);
      if (!check.passed) throw Error(`Live verification failed: ${route} (${response.status})`);
    }
    report.passed = true;
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    report.passed = false; report.error = error.message; process.exitCode = 1;
    console.error(error.message);
  } finally {
    const target = path.resolve(__dirname, '../../docs/p11/generated');
    fs.mkdirSync(target, { recursive: true });
    fs.writeFileSync(path.join(target, 'smoke.json'), JSON.stringify(report, null, 2));
  }
})();
