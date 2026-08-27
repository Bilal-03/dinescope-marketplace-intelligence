# Methodology

## Source contract

- Source file: `zomato_business_complete.csv`
- SHA-256: `fc5ca0ca1043e3cfb17ab467a7b87bbcc0a516cd766e962b4850a202d5a88be7`
- Grain used by the product: one source row per unique Order ID
- Date interpretation: explicit `%m/%d/%Y` parsing
- Observed window: 4 October 2017 through 26 June 2020

## Valid transaction rule

A business KPI transaction must have a non-null order ID, a parsed date, a true `Sales Amount Valid` flag, non-null sales greater than zero, and INR currency. Exclusions are preserved in quality aggregates and are never silently deleted.

## Customer definitions

- Active customer: at least one valid transaction in the filtered scope.
- New customer: first observed valid transaction in the filtered source-market scope falls in the selected period.
- Repeat customer: at least two valid transactions in the filtered scope.
- Repeat rate: repeat customers divided by active customers.
- Cohort retention: customers active at cohort age M divided by customers first observed in that cohort month.

RFM-style lifecycle segments use transparent ordering signals only. They do not claim app engagement, customer intent or causal response to a campaign.

## Restaurant identity and cuisine allocation

The pipeline emits reviewable cuisine and restaurant-name mappings. Cuisine tokens are trimmed, case-normalized, mapped through a small explicit alias set and screened for known non-cuisine labels. Each transaction's unique canonical cuisines receive an equal `1/n` share of its transaction and sales value. Allocated transaction totals therefore reconcile exactly to cuisine-covered valid transactions.

Restaurant names use deliberately conservative normalization: Unicode accents, case, punctuation and ampersands are standardized, without fuzzy matching or stripping outlet locations. Because only 123 of 148,541 restaurant IDs repeat, the product reports observed normalized listings as supply context and does not claim durable outlet or restaurant performance.

## Cuisine opportunity eligibility and score

The default cuisine-market comparison uses the same equal-length windows as Market Intelligence. A pair is eligible with at least 100 allocated current transactions, 50 allocated comparison transactions and calculable growth. Its 0–100 investigation signal combines demand (25%), growth (25%), customer reach (20%), demand-to-listing gap (15%) and quality coverage (15%), then discounts the result for medium or low evidence confidence. Component values are normalized within the active period, so the signal is a relative prioritization tool—not a forecast or proof of unmet supply.

## Known limitations

Restaurant IDs rarely repeat, restaurant ratings cover roughly 41% of rows, and menu fields cover roughly 8%. Cuisine labels and listing counts are observational, and equal allocation assumes each listed cuisine contributed equally to the transaction. Recommended actions are hypotheses for validation.

## Location mapping and market eligibility

The pipeline generates `data/mappings/location_mapping.csv`, with one row per raw label plus its cleaned city, metro region, state, confidence, review status and source-row count. Comma-delimited locality labels use the final city token only when the result is covered by a reviewed metro rule. Explicit aliases handle known variants such as `Noida-1`, `North-goa` and historical city names. Unknown locations remain Unknown.

The default market-growth view compares the latest 365 observed days with the immediately preceding 365 days. Year filters compare the observed calendar span with the same dates one year earlier. A market is eligible by default only when it has at least 200 current transactions, at least 100 comparison transactions and a calculable growth rate. The UI lets users raise or lower the current threshold while preserving a minimum comparison base.

Confidence combines current sample size and mapping coverage. High confidence requires at least 500 current transactions and at least 80% high-confidence mapped rows; medium requires at least 200 transactions; smaller markets remain low confidence.
