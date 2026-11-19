const fs = require('node:fs');
const path = require('node:path');
const value = process.env.NEXT_PUBLIC_API_URL;
if (!value || new URL(value).protocol !== 'https:') throw Error('A public HTTPS NEXT_PUBLIC_API_URL repository variable is required');
const target = path.resolve('.vercel', `.env.${process.argv[2]}.local`);
// Public client configuration must not compile an unreadable secret placeholder.
// Other environment variables from Vercel are preserved without being printed.
const lines = fs.readFileSync(target, 'utf8').split(/\r?\n/).filter(line => !/^NEXT_PUBLIC_API_URL=/.test(line));
lines.push(`NEXT_PUBLIC_API_URL=${JSON.stringify(value)}`);
fs.writeFileSync(target, lines.join('\n'));
console.log('Prepared the public backend URL; private environment variables were left unchanged.');
