# PlateLens

PlateLens is an interactive food-delivery marketplace intelligence product for Product and Growth teams. It connects customer acquisition, repeat behavior, cohort retention and data reliability so teams can identify where evidence supports action—and where the source is too weak to justify a claim.

This is an independent portfolio case study created from a public or synthetic food-delivery dataset. It is not affiliated with, endorsed by, or based on internal data from Zomato, Swiggy, or another food-delivery company.

## What is working

- Executive marketplace overview with audited KPIs and deterministic decision brief
- Product/Growth module with acquisition-versus-return trends, transaction frequency, lifecycle segmentation, cohort-retention heatmap and CSV export
- Market & Demand Intelligence with cleaned metro markets, equal-length growth comparisons, eligibility controls, confidence labels, a scale-versus-growth quadrant and CSV export
- Data Reliability Center with transaction reconciliation, source fingerprint and field-coverage warnings
- Global source-market and year filters with reset and designed empty states
- Deployment-ready private-site authentication hooks and server-side Admin/Analyst role resolution
- Automated reconciliation tests for the source contract and core customer metrics
- Auditable 822-label locality-to-market mapping with explicit review status

See [STATUS.md](./STATUS.md) for the phase checklist and next build order.

## Architecture

The attached implementation plan recommended Streamlit. PlateLens uses a hybrid architecture instead: Python prepares reproducible, audited aggregate analytics; a typed React/Vinext interface provides the polished interactive experience; and the deployment output is Cloudflare Worker-compatible. Raw customer-level records and addresses are not shipped to the browser.

```text
Source CSV
  → Python schema + validity audit
  → deployment-safe aggregate JSON
  → typed metric/filter layer
  → React analytics workspace
  → private Sites deployment
```

The original CSV is intentionally excluded from source control. Generate the aggregate file and reviewable location mapping locally with:

```bash
python3 scripts/build_analytics.py /path/to/zomato_business_complete.csv app/data/analytics.json
```

## Metric guardrails

- Valid transactions require an order ID, parsed `MM/DD/YYYY` date, true source-validity flag, positive sales and INR currency.
- “Average transaction value” is used instead of AOV because the source grain is not independently verified.
- Repeat customer rate is not presented as retention; retention uses acquisition cohorts and month age.
- Restaurant performance claims are suppressed because most restaurant IDs appear once.
- Market growth rankings require current and comparison-period sample thresholds; tiny bases are not allowed to lead the ranking.
- Delivery, cancellation, discount, commission, funnel and campaign metrics are absent because the fields do not exist.

## Local development

Requires Node.js 22.13+ and Python with the pinned packages in `requirements.txt`.

```bash
npm install
npm run dev
npm test
npm run build
```

Set `PLATELENS_ADMIN_EMAILS` to a comma-separated allowlist when Admin labels are needed. All other authenticated visitors resolve to Analyst; unauthenticated local previews resolve to Preview.
