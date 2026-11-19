const fs = require('node:fs');
const path = require('node:path');
const expected = process.env.NEXT_PUBLIC_API_URL;
if (!expected) throw Error('NEXT_PUBLIC_API_URL is required for bundle verification');
function files(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const full = path.join(dir, entry.name);
    return entry.isDirectory() ? files(full) : entry.name.endsWith('.js') ? [full] : [];
  });
}
const chunks = files(path.resolve('.vercel/output/static/_next'));
let found = false;
for (const file of chunks) {
  const code = fs.readFileSync(file, 'utf8');
  if (code.includes('[SENSITIVE]') || code.includes('[REDACTED]')) throw Error('A secret placeholder was compiled into a public JavaScript bundle');
  if (code.includes(expected)) found = true;
}
if (!found) throw Error('The public client bundle does not contain the configured backend URL');
console.log(`Verified backend configuration in ${chunks.length} public JavaScript chunks.`);
