import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const portfolio = await readFile(new URL('../docs/portfolio_case_study.md', import.meta.url), 'utf8');
const readiness = await readFile(new URL('../docs/release_readiness.md', import.meta.url), 'utf8');

test('portfolio case study is evidence-backed and bounded', () => {
  assert.match(portfolio, /150,281/);
  assert.match(portfolio, /148,668/);
  assert.match(portfolio, /₹986,564,268/);
  assert.match(portfolio, /Repeat rate/);
  assert.match(portfolio, /not affiliated with a food-delivery company/);
  assert.match(portfolio, /delivery-time, cancellation, discount, commission, funnel or campaign/);
  assert.match(portfolio, /Decision Lab/);
});

test('release readiness keeps public access as an explicit owner decision', () => {
  assert.match(readiness, /Private production workspace/);
  assert.match(readiness, /Public unauthenticated deployment/);
  assert.match(readiness, /Pending owner approval/);
  assert.match(readiness, /Decision:\s+\[ \] Keep private/);
  assert.match(readiness, /server-backed team sharing/);
});

test('representative screenshots are present as image artifacts', async () => {
  for (const filename of ['01-overview.jpg', '02-decision-lab.jpg', '03-cuisine-opportunity.jpg']) {
    const bytes = await readFile(new URL(`../docs/screenshots/${filename}`, import.meta.url));
    assert.ok(bytes.length > 10_000, `${filename} should be a real capture, not an empty placeholder`);
    assert.deepEqual([...bytes.subarray(0, 3)], [255, 216, 255]);
  }
});
