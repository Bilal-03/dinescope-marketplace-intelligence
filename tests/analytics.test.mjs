import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const analytics = JSON.parse(await readFile(new URL('../app/data/analytics.json', import.meta.url), 'utf8'));
const all = analytics.scopes['All markets|All years'];

test('source contract and transaction reconciliation are exact', () => {
  assert.equal(analytics.aggregate_version, '1.1.0');
  assert.equal(analytics.source.rows, 150_281);
  assert.equal(analytics.source.columns, 36);
  assert.equal(analytics.source.expected_columns, 36);
  assert.equal(analytics.source.schema_matches, true);
  assert.equal(analytics.source.date_format, 'MM/DD/YYYY');
  assert.equal(analytics.quality.valid_transactions, 148_668);
  assert.equal(analytics.quality.valid_transactions + analytics.quality.excluded_transactions, analytics.quality.raw_rows);
  assert.equal(analytics.quality.missing_rating_rows, 88_755);
  assert.equal(analytics.quality.missing_menu_attribute_rows, 138_145);
  assert.equal(analytics.quality.missing_rating_rows, Math.round(analytics.quality.raw_rows * (1 - analytics.quality.rating_coverage)));
  assert.equal(analytics.quality.missing_menu_attribute_rows, Math.round(analytics.quality.raw_rows * (1 - analytics.quality.menu_coverage)));
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

test('location mapping reconciles every source row', () => {
  const mapping = analytics.location_mapping;
  assert.equal(mapping.raw_labels, 822);
  assert.equal(mapping.mapped_rows + mapping.unknown_rows, analytics.source.rows);
  assert.ok(mapping.high_confidence_rows <= mapping.mapped_rows);
  assert.ok(analytics.filters.markets.includes('Bangalore'));
  assert.ok(analytics.filters.markets.includes('Delhi'));
  assert.ok(analytics.filters.markets.every((market) => !market.includes(',')));
});

test('market eligibility and concentration rules reconcile', () => {
  const view = analytics.market_views['All years'];
  const eligible = view.markets.filter((row) => row.eligible_default);
  assert.equal(view.summary.eligible_markets, eligible.length);
  assert.ok(eligible.every((row) => row.orders >= 200 && row.previous_orders >= 100 && row.growth_orders !== null));
  const topFiveShare = view.markets.slice(0, 5).reduce((sum, row) => sum + row.order_share, 0);
  assert.ok(Math.abs(topFiveShare - view.summary.top_five_concentration) < 1e-12);
  for (const row of view.markets.slice(0, 20)) {
    assert.equal(row.monthly_orders.reduce((sum, point) => sum + point.orders, 0), row.orders);
  }
});

test('cuisine taxonomy is explicit and proportional allocation reconciles', () => {
  assert.equal(analytics.cuisine_mapping.raw_tokens, 126);
  assert.equal(analytics.cuisine_mapping.canonical_cuisines, 110);
  assert.equal(analytics.cuisine_mapping.excluded_token_rows, 22);
  for (const view of Object.values(analytics.cuisine_views)) {
    assert.ok(Math.abs(view.allocated_order_total - view.covered_order_count) < 1e-9);
  }
});

test('cuisine opportunities obey evidence and score boundaries', () => {
  for (const view of Object.values(analytics.cuisine_views)) {
    assert.ok(view.pairs.every((row) => row.opportunity_score >= 0 && row.opportunity_score <= 100));
    const eligible = view.pairs.filter((row) => row.eligible_default);
    assert.equal(view.summary.eligible_pairs, eligible.length);
    assert.ok(eligible.every((row) => row.allocated_orders >= 100 && row.previous_allocated_orders >= 50 && row.growth !== null));
  }
});

test('restaurant evidence is not misrepresented as durable outlet performance', () => {
  assert.equal(analytics.restaurant_mapping.restaurant_ids, 148_541);
  assert.equal(analytics.restaurant_mapping.restaurant_ids_repeated, 123);
  assert.ok(analytics.restaurant_mapping.restaurant_ids_repeated / analytics.restaurant_mapping.restaurant_ids < 0.001);
});
