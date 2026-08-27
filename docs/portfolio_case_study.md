# DineScope — Food Marketplace Intelligence

## Case-study snapshot

**Role:** Product manager / product-minded engineer  
**Audience:** Product, Growth, Marketplace, Category and City Operations teams  
**Product:** An interactive decision-intelligence platform that helps Product and Growth teams uncover customer, market, restaurant, and cuisine opportunities from food-delivery data.
**Status:** Public read-only Streamlit deployment; aggregate-only portfolio release is live.

This is an independent portfolio case study. It is not affiliated with a food-delivery company, endorsed by Zomato or Swiggy, or based on internal company data.

DineScope is designed around a practical product question: *where should a marketplace team investigate next, and how much confidence should it have in the evidence?* It connects customer behavior, market demand, cuisine opportunity and source reliability in one workspace. The interface makes uncertainty visible at the same moment that it presents an opportunity, so a high ranking cannot be mistaken for a proven causal recommendation.

## The problem

Marketplace teams rarely struggle to find a chart. They struggle to reconcile competing signals:

- Growth can be strong because of a small or newly mapped market.
- A cuisine can look under-supplied because listings and demand are measured at different grains.
- A repeat rate can be mistaken for retention even when cohort maturity is unknown.
- A polished dashboard can hide missing ratings, menu coverage or invalid transactions.

The source file contains enough customer, order, location, cuisine and restaurant context to explore these questions, but not enough operational fields to claim delivery speed, cancellation, discount, commission, funnel or campaign performance. DineScope therefore makes the source contract part of the product rather than burying it in an appendix.

## What was built

The product is a responsive, keyboard-usable analytics workspace with five connected modules:

1. **Overview** — audited marketplace KPIs, customer mix, monthly acquisition-versus-return trend and a deterministic decision brief.
2. **Customers** — repeat behavior, frequency, lifecycle segments, cohort retention and a downloadable segment evidence table.
3. **Markets** — cleaned metro demand, equal-length current-versus-comparison growth, scale-versus-growth quadrant, eligibility thresholds, mapping coverage and confidence.
4. **Cuisines** — canonical taxonomy, additive multi-cuisine allocation, cuisine-market opportunity signals, observed listing context, evidence thresholds and CSV export.
5. **Decision Lab** — configurable demand, growth, reach, gap and data-quality weights; confidence discounting; presets stored locally; comparison; rank movement; and a decision-brief export.

The **Data Reliability Center** is intentionally cross-cutting. It exposes reconciliation, field coverage, source fingerprint and mapping warnings at the point where a user interprets a metric.

## Evidence at a glance

The current aggregate is generated from 150,281 source rows and 36 columns.

| Evidence | Verified value | Product implication |
| --- | ---: | --- |
| Valid transactions | 148,668 | The KPI layer uses a transparent validity rule and preserves 1,613 exclusions. |
| Gross valid sales | ₹986,564,268 | Sales are reported as gross valid INR sales, not net revenue. |
| Active customers | 77,584 | Customer scope is based on distinct customers with at least one valid transaction. |
| Repeat rate | 56.6% | Repeat means at least two valid transactions in the selected scope; it is not retention. |
| Rating coverage | 41.0% | Quality context stays visible before a rating-led conclusion is made. |
| Menu coverage | 8.1% | Menu-based supply comparisons are explicitly weak. |
| Raw market labels | 822 | Localities are mapped to reviewed metro labels, with Unknown retained. |
| Cuisine coverage | 98.9% | Multi-cuisine transactions are allocated proportionally so covered demand reconciles. |
| Repeated restaurant IDs | 123 of 148,541 | Restaurant evidence is presented as observed listings, not durable outlet performance. |

The source window is 4 October 2017 through 26 June 2020. Dates are parsed explicitly as `MM/DD/YYYY`; duplicate order IDs and invalid dates are zero in the audited source.

## Product decisions and trade-offs

### Separate repeat behavior from retention

Repeat rate answers “how many active customers ordered at least twice in this scope?” Cohort retention answers “what share of a first-observed cohort returned at month age *m*?” Keeping both avoids overstating marketplace habit from a single aggregate number.

### Use evidence thresholds before ranking

Market growth requires equal-length windows and minimum current/comparison samples. Cuisine-market opportunities require at least 100 allocated current transactions and 50 comparison transactions. Tiny bases can remain visible for exploration, but they cannot lead the default recommendation set.

### Make cuisine demand additive

When an order contains multiple cuisines, each unique canonical cuisine receives an equal `1/n` share of the order and sales value. Allocated demand therefore reconciles exactly to cuisine-covered valid transactions. This is an assumption for directional planning, not a claim about item-level mix.

### Treat restaurant names conservatively

Normalization standardizes accents, case, punctuation and ampersands without fuzzy matching or stripping outlet locations. Since restaurant IDs rarely repeat, the interface reports observed normalized listings and coverage context instead of pretending to measure restaurant-level performance.

### Do not fabricate unavailable operations metrics

There are no delivery-time, cancellation, discount, commission, funnel or campaign fields in the source. Those areas remain explicitly out of scope until a source with the required grain and definitions is available.

## Technical architecture

```text
Source CSV
  → Python schema + validity audit
  → deployment-safe aggregate JSON + reviewable mapping CSVs
  → typed metric/filter layer
  → React/Vinext analytics workspace
  → private Cloudflare Worker-compatible Sites deployment
```

Raw customer-level records and addresses are not shipped to the browser. The checked-in aggregate contains only the measures and evidence rows needed by the interface. The build is reproducible through `scripts/audit_source.py` and `scripts/build_analytics.py`; the source fingerprint and definitions travel with the aggregate.

## What each team can do with it

- **Product:** distinguish acquisition volume from repeat behavior, inspect cohort maturity and frame activation hypotheses without calling them causal results.
- **Growth:** size lifecycle segments, identify first-to-second-order opportunities and export evidence for a test brief.
- **Marketplace:** compare market scale and momentum while seeing mapping coverage and confidence.
- **Category:** find cuisine-market pairs worth validating, with demand, growth, reach, listing context and quality coverage in one row.
- **City Operations:** use locality-to-metro mapping and sample thresholds to decide where a qualitative supply or coverage audit is warranted.

Every recommendation is an investigation signal. The product does not claim incremental lift, unmet supply, profitability or operational causality from this dataset alone.

## Verification and engineering quality

The current release passes:

- 16 automated reconciliation, interface-contract and portfolio-package tests (`npm test`).
- ESLint and a production build (`npm run lint`, `npm run build`).
- A repeatable performance budget (`npm run check:performance`) covering the aggregate payload, client JavaScript and client CSS.
- Accessibility contracts for named navigation and controls, explicit button types, visible keyboard focus, keyboard-selectable evidence rows and export affordances.

The active budgets are 1.3 MB for the aggregate, 650 KB raw / 180 KB gzip-sum for client JavaScript, and 60 KB raw / 20 KB gzip-sum for client CSS. These are regression guardrails, not promises about a user's network speed.

## Limitations and responsible interpretation

- The dataset is an independent portfolio input and is not internal company data.
- The source grain is not independently verified, so the product says “average transaction value” rather than AOV.
- Customer identity and first-observed cohorts are source-relative; they are not a complete customer 360.
- Ratings cover roughly two-fifths of rows and menu fields roughly one-twelfth.
- Cuisine allocation assumes equal contribution from each listed cuisine.
- Listing counts are observational and do not prove availability, quality or unmet demand.
- Decision Lab weights change prioritization inside the eligible set; they do not change the underlying facts or create a forecast.

## Portfolio presentation plan

The representative screenshots in [`docs/screenshots/`](./screenshots/) show the overview, Decision Lab and cuisine opportunity surfaces using the private production build:

- [`01-overview.jpg`](./screenshots/01-overview.jpg) — audited KPIs, marketplace momentum and the decision brief.
- [`02-decision-lab.jpg`](./screenshots/02-decision-lab.jpg) — explicit weighting, evidence guardrails and the current investigation lead.
- [`03-cuisine-opportunity.jpg`](./screenshots/03-cuisine-opportunity.jpg) — canonical cuisine coverage, thresholds and demand-to-coverage context.

They are intended to demonstrate the interaction model and evidence treatment, not to expose raw customer records.

For a public portfolio page, the recommended framing is:

> “I built a deployment-ready marketplace intelligence product that makes customer growth, demand opportunity and data reliability legible in one workflow. The product is intentionally conservative: it exposes missing evidence, enforces minimum samples and labels directional signals as hypotheses.”

The release checklist in [`docs/release_readiness.md`](./release_readiness.md) records what is ready now, what still needs owner sign-off and what must be rechecked before any public access change.
