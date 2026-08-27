import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const analytics = JSON.parse(await readFile(new URL('../app/data/analytics.json', import.meta.url), 'utf8'));
const all = analytics.scopes['All markets|All years'];

test('source contract and transaction reconciliation are exact', () => {
  assert.equal(analytics.source.rows, 150_281);
  assert.equal(analytics.source.columns, 36);
  assert.equal(analytics.source.date_format, 'MM/DD/YYYY');
  assert.equal(analytics.quality.valid_transactions, 148_668);
  assert.equal(analytics.quality.valid_transactions + analytics.quality.excluded_transactions, analytics.quality.raw_rows);
  assert.equal(analytics.quality.duplicate_order_ids, 0);
  assert.equal(analytics.quality.invalid_dates, 0);
});

test('audited commercial metrics reconcile', () => {
  assert.equal(all.metrics.gross_sales, 986_564_268);
  assert.equal(all.metrics.active_customers, 77_584);
  assert.equal(all.metrics.repeat_customers, 43_924);
  assert.ok(Math.abs(all.metrics.repeat_rate - 43_924 / 77_584) < 1e-12);
  assert.ok(Math.abs(all.metrics.average_transaction_value - 986_564_268 / 148_668) < 1e-9);
});

test('customer distributions reconcile to active customers', () => {
  assert.equal(all.frequency.reduce((sum, row) => sum + row.customers, 0), all.metrics.active_customers);
  assert.equal(all.segments.reduce((sum, row) => sum + row.customers, 0), all.metrics.active_customers);
  assert.ok(all.cohorts.every((row) => row.retention[0] === 100));
});

test('every advertised filter combination has a scope', () => {
  for (const market of analytics.filters.markets) {
    for (const period of analytics.filters.periods) {
      assert.ok(analytics.scopes[`${market}|${period}`], `missing ${market}|${period}`);
    }
  }
});
