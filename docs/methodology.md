# Methodology

## Source contract

- Aggregate contract version: `1.3.0`
- Source file: `zomato_business_complete.csv`
- SHA-256: `fc5ca0ca1043e3cfb17ab467a7b87bbcc0a516cd766e962b4850a202d5a88be7`
- Grain used by the product: one source row per unique Order ID
- Date interpretation: explicit `%m/%d/%Y` parsing
- Observed window: 4 October 2023 through 26 June 2026

The aggregate builder fails before processing when required source fields are missing or the input does not contain exactly the audited 36 columns. The published artifact records `expected_columns` and `schema_matches` so the Python adapter and Streamlit release checks can fail loudly on schema drift.

## Two-stage transaction inclusion rule

A source-valid transaction must have a non-null order ID, a parsed date, a true `Sales Amount Valid` flag, non-null sales greater than zero, and INR currency. This source-valid count is preserved as the raw audit baseline.

Headline project analytics use a second, deterministic plausibility rule: the source-valid row must also have a positive `Order Value` at or below **₹7,500**. The cutoff is the rounded 1.5×IQR upper fence of the source-valid distribution (Q1 ₹176, Q3 ₹3,065, raw fence ₹7,398.50). Values above the cutoff are retained in a local exclusion audit and are not silently deleted from the original source.

The current source contains 148,668 source-valid transactions. The cleaned analytical scope includes 126,519 transactions and excludes 22,149 high-value rows. Source-valid sales of ₹986,564,268 reconcile to ₹139,532,057 of included filtered sales plus ₹847,032,211 of excluded high-value sales.

Coverage is measured against all 150,281 source rows. The published contract therefore carries explicit missing-field counts—88,755 rows without a rating and 138,145 rows without menu attributes—in addition to the coverage percentages. These counts must reconcile to `round(raw_rows × (1 − coverage))`.

## Customer definitions

- Included analytical transaction: a source-valid transaction that passes the `Order Value ≤ ₹7,500` plausibility rule.
- Active customer: at least one included analytical transaction in the filtered scope.
- New customer: first observed included analytical transaction in the filtered source-market scope falls in the selected period.
- Repeat customer: at least two included analytical transactions in the filtered scope.
- Repeat rate: repeat customers divided by active customers.
- Cohort retention: customers active at cohort age M divided by customers first observed in that cohort month.

RFM-style lifecycle segments use transparent ordering signals only. They do not claim app engagement, customer intent or causal response to a campaign.

## Restaurant identity and cuisine allocation

The pipeline emits reviewable cuisine and restaurant-name mappings. Cuisine tokens are trimmed, case-normalized, mapped through a small explicit alias set and screened for known non-cuisine labels. Each included transaction's unique canonical cuisines receive an equal `1/n` share of its transaction and filtered sales value. Allocated transaction totals therefore reconcile exactly to cuisine-covered included transactions.

Restaurant names use deliberately conservative normalization: Unicode accents, case, punctuation and ampersands are standardized, without fuzzy matching or stripping outlet locations. Because only 123 of 148,541 restaurant IDs repeat, the product reports observed normalized listings as supply context and does not claim durable outlet or restaurant performance.

## Cuisine opportunity eligibility and score

The default cuisine-market comparison uses the same equal-length windows as Market Intelligence. A pair is eligible with at least 100 allocated current transactions, 50 allocated comparison transactions and calculable growth. Its 0–100 investigation signal combines demand (25%), growth (25%), customer reach (20%), demand-to-listing gap (15%) and quality coverage (15%), then discounts the result for medium or low evidence confidence. Component values are normalized within the active period, so the signal is a relative prioritization tool—not a forecast or proof of unmet supply.

## Known limitations

Restaurant IDs rarely repeat, restaurant ratings cover roughly 41% of rows, and menu fields cover roughly 8%. The plausibility filter excludes 14.9% of source-valid transactions and 85.9% of source-valid sales because the source contains a heavy upper tail; filtered sales and order-value metrics are labelled accordingly. Cuisine labels and listing counts are observational, and equal allocation assumes each listed cuisine contributed equally to the transaction. Recommended actions are hypotheses for validation.

## Decision Lab scenarios

Decision Lab starts from the balanced cuisine opportunity signal but recalculates a pair's relative percentile score inside the active eligible set. Users can change weights for demand scale, growth momentum, customer reach, coverage gap and data quality; weights are normalized to 100% for calculation. An optional confidence adjustment applies the same High (1.0), Medium (0.85) and Low (0.65) factors used by the default opportunity view. Scenario presets are stored locally on the user's device, and the export includes the active scope, threshold, weights, confidence setting and ranked evidence rows. Presets are not a shared source of truth until a server-backed collaboration layer is introduced.

## Interaction and performance guardrails

The Streamlit AppTest suite requires named navigation and Decision Lab controls, stable filter state, export wiring and error-free rendering for every public workspace. Aggregate checks keep the published analytics payload below the documented 1.3 MB budget. These are engineering guardrails for regressions, not claims about end-user network speed.

## Location mapping and market eligibility

The pipeline generates `data/mappings/location_mapping.csv`, with one row per raw label plus its cleaned city, metro region, state, confidence, review status and source-row count. Comma-delimited locality labels use the final city token only when the result is covered by a reviewed metro rule. Explicit aliases handle known variants such as `Noida-1`, `North-goa` and historical city names. Unknown locations remain Unknown.

The default market-growth view compares the latest 365 observed days with the immediately preceding 365 days. Year filters compare the observed calendar span with the same dates one year earlier. A market is eligible by default only when it has at least 200 current transactions, at least 100 comparison transactions and a calculable growth rate. The UI lets users raise or lower the current threshold while preserving a minimum comparison base.

Confidence combines current sample size and mapping coverage. High confidence requires at least 500 current transactions and at least 80% high-confidence mapped rows; medium requires at least 200 transactions; smaller markets remain low confidence.
