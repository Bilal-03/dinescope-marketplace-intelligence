# PlateLens

PlateLens is an interactive food-delivery marketplace intelligence product for Product and Growth teams. It connects customer acquisition, repeat behavior, cohort retention and data reliability so teams can identify where evidence supports action—and where the source is too weak to justify a claim.

This is an independent portfolio case study created from a public or synthetic food-delivery dataset. It is not affiliated with, endorsed by, or based on internal data from Zomato, Swiggy, or another food-delivery company.

Live public Streamlit app: [platelens-food-delivery-intelligence.streamlit.app](https://platelens-food-delivery-intelligence.streamlit.app/)

## What is working

- Executive marketplace overview with audited KPIs and deterministic decision brief
- Product/Growth module with acquisition-versus-return trends, transaction frequency, lifecycle segmentation, cohort-retention heatmap and CSV export
- Market & Demand Intelligence with cleaned metro markets, equal-length growth comparisons, eligibility controls, confidence labels, a scale-versus-growth quadrant and CSV export
- Restaurant & Cuisine Opportunity with canonical cuisine taxonomy, additive multi-cuisine demand allocation, evidence thresholds, opportunity signals, heatmap and CSV export
- Decision Lab with configurable demand/growth/reach/gap/quality weights, confidence guardrails, scenario comparison, local presets, rank movement and decision-brief export
- Accessibility and performance hardening with keyboard-selectable evidence rows, named controls, interaction contract tests and a repeatable bundle budget check
- Data Reliability Center with transaction reconciliation, source fingerprint and field-coverage warnings
- Global source-market and year filters with reset and designed empty states
- Deployment-ready private-site authentication hooks and server-side Admin/Analyst role resolution
- Automated reconciliation tests for source, customer, market, cuisine and opportunity-score contracts
- Auditable locality, cuisine and conservative restaurant-name mappings with explicit coverage context
- Portfolio-ready case study, evidence boundaries, representative screenshots and a private/public release gate
- Public Streamlit app with six aggregate-only workspaces, evidence-table exports and full staged visual/interaction parity

See [STATUS.md](./STATUS.md) for the phase checklist and next build order.

The Phase 8 evidence package is in [docs/portfolio_case_study.md](./docs/portfolio_case_study.md), with access, privacy and deployment sign-off tracked in [docs/release_readiness.md](./docs/release_readiness.md).

The Streamlit implementation and public-release sequence are documented in [docs/streamlit_public_deployment_plan.md](./docs/streamlit_public_deployment_plan.md). Streamlit Phases 0–5 (data-contract hardening, parity shell, Overview/Customer Growth, Reliability, Market Demand, Cuisine Opportunity, restaurant evidence and session-only Decision Lab parity) are complete; the React/Vinext app remains the visual reference while server-backed scenario sharing stays an explicit future capability.

The project owner approved publishing the deployment-safe aggregate and mapping artifacts for the public read-only app. Raw order/customer records, secrets and private Sites metadata remain excluded. See [docs/public_data_boundary.md](./docs/public_data_boundary.md).

## Architecture

PlateLens uses a dual-interface architecture: Python prepares one reproducible audited aggregate; Streamlit provides the public read-only analytics product; and the typed React/Vinext interface remains the polished private reference experience. Raw customer-level records and addresses are not shipped to either frontend.

```text
Source CSV
  → Python schema + validity audit
  → deployment-safe aggregate JSON
  ├→ Python metric adapter → public Streamlit Community Cloud app
  └→ typed metric/filter layer → private React/Sites reference app
```

The original CSV is intentionally excluded from source control. Generate the aggregate file and reviewable location, cuisine and restaurant-name mappings locally with:

```bash
python3 scripts/build_analytics.py /path/to/zomato_business_complete.csv app/data/analytics.json
```

## Metric guardrails

- Valid transactions require an order ID, parsed `MM/DD/YYYY` date, true source-validity flag, positive sales and INR currency.
- “Average transaction value” is used instead of AOV because the source grain is not independently verified.
- Repeat customer rate is not presented as retention; retention uses acquisition cohorts and month age.
- Restaurant performance claims are suppressed because most restaurant IDs appear once.
- Multi-cuisine transactions are split equally across canonical cuisines, so allocated transaction totals remain additive.
- Cuisine opportunity scores prioritize investigation; they do not prove unmet supply or forecast causal impact.
- Decision Lab scores normalize each selected dimension within the filtered eligible set; changing weights changes prioritization, not the underlying metrics.
- Market growth rankings require current and comparison-period sample thresholds; tiny bases are not allowed to lead the ranking.
- Delivery, cancellation, discount, commission, funnel and campaign metrics are absent because the fields do not exist.

## Local development

Requires Node.js 22.13+ and Python with the pinned packages in `requirements.txt`.

Public Streamlit app:

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest tests/test_streamlit_lib.py
.venv/bin/streamlit run streamlit_app.py
```

The public deployment is configured from the `main` branch, uses Python 3.11 and Streamlit 1.62.0, and loads only the checked-in deployment-safe aggregate. For staged validation, set `PLATELENS_FEATURE_FLAGS` to a comma-separated allowlist such as `shell_v2,markets_v2`; leaving it blank enables all known flags.

Private React reference app:

```bash
npm install
npm run dev
npm test
npm run check:performance
npm run build
```

Set `PLATELENS_ADMIN_EMAILS` to a comma-separated allowlist when Admin labels are needed. All other authenticated visitors resolve to Analyst; unauthenticated local previews resolve to Preview.
