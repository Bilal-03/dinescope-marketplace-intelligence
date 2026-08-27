import { gzip as gzipCallback } from 'node:zlib';
import { promisify } from 'node:util';
import { readFile, readdir, stat } from 'node:fs/promises';
import { join, relative } from 'node:path';

const gzip = promisify(gzipCallback);
const root = process.cwd();
const limits = {
  aggregate: 1_300_000,
  clientJsRaw: 650_000,
  clientJsGzip: 180_000,
  clientCssRaw: 60_000,
  clientCssGzip: 20_000,
};

async function filesIn(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await filesIn(path));
    else files.push(path);
  }
  return files;
}

async function byteTotals(paths) {
  const sizes = await Promise.all(paths.map(async (path) => {
    const contents = await readFile(path);
    return { raw: contents.byteLength, gzip: (await gzip(contents)).byteLength };
  }));
  return sizes.reduce((total, size) => ({ raw: total.raw + size.raw, gzip: total.gzip + size.gzip }), { raw: 0, gzip: 0 });
}

const aggregatePath = join(root, 'app/data/analytics.json');
const staticPath = join(root, 'dist/client/_next/static');
const aggregateBytes = (await stat(aggregatePath)).size;
const staticFiles = await filesIn(staticPath);
const jsTotals = await byteTotals(staticFiles.filter((path) => path.endsWith('.js')));
const cssTotals = await byteTotals(staticFiles.filter((path) => path.endsWith('.css')));
const checks = [
  ['analytics aggregate', aggregateBytes, limits.aggregate],
  ['client JavaScript raw', jsTotals.raw, limits.clientJsRaw],
  ['client JavaScript gzip sum', jsTotals.gzip, limits.clientJsGzip],
  ['client CSS raw', cssTotals.raw, limits.clientCssRaw],
  ['client CSS gzip sum', cssTotals.gzip, limits.clientCssGzip],
];

for (const [name, actual, limit] of checks) {
  const passed = actual <= limit;
  console.log(`${passed ? 'PASS' : 'FAIL'} ${name}: ${actual.toLocaleString('en-IN')} bytes (budget ${limit.toLocaleString('en-IN')})`);
  if (!passed) process.exitCode = 1;
}

console.log(`Audited ${staticFiles.length} client static assets under ${relative(root, staticPath)}.`);
