const fs = require('node:fs');
const path = require('node:path');
const base = process.env.DEPLOYMENT_URL?.replace(/\/$/, '');
const expectedCommit = process.env.GITHUB_SHA;
if (!base || !expectedCommit) throw Error('DEPLOYMENT_URL and GITHUB_SHA are required');
const report = { testedAt: new Date().toISOString(), url: base, expectedCommit, checks: [] };
(async () => {
  try {
    for (const route of ['/version.json', '/', '/catalog', '/wizard', '/compare']) {
      const headers = process.env.VERCEL_AUTOMATION_BYPASS_SECRET
        ? { 'x-vercel-protection-bypass': process.env.VERCEL_AUTOMATION_BYPASS_SECRET }
        : {};
      const response = await fetch(base + route, { headers, signal: AbortSignal.timeout(30000) });
      const check = { route, status: response.status, passed: response.ok };
      if (route === '/version.json' && response.ok) {
        check.version = await response.json();
        check.passed = check.version.commit === expectedCommit;
      }
      if (route === '/catalog' && response.ok) {
        const html = await response.text();
        const scripts = [...html.matchAll(/<script[^>]+src="([^"]+\.js(?:\?[^"]*)?)"/g)].map(match => match[1]);
        let apiConfigured = false;
        const expectedApi = process.env.NEXT_PUBLIC_API_URL;
        if (!expectedApi) throw Error('NEXT_PUBLIC_API_URL is required for client verification');
        for (const script of new Set(scripts)) {
          const url = new URL(script, base);
          if (url.origin !== new URL(base).origin) continue;
          const chunk = await fetch(url, { headers, signal: AbortSignal.timeout(30000) });
          if (!chunk.ok) throw Error('A deployed client chunk is unavailable');
          const source = await chunk.text();
          if (source.includes('[SENSITIVE]') || source.includes('[REDACTED]')) throw Error('The deployed client contains an invalid environment placeholder');
          if (source.includes(expectedApi)) apiConfigured = true;
        }
        check.apiConfigured = apiConfigured;
        check.passed = check.passed && apiConfigured;
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
