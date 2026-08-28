# DineScope implementation status

Updated: 28 August 2026

## Current release: Public Streamlit full-parity baseline

- [x] Product framing, DineScope brand identity, repository and deployment-ready shell
- [x] Source audit, schema/date contract, transaction exclusions, checksum and metric definitions
- [x] Reproducible aggregate pipeline for deployment-safe analytics data
- [x] Core KPIs, repeat logic, lifecycle segmentation and cohort-retention calculations
- [x] Responsive design system, global filters, metric dictionary and empty/planned states
- [x] Executive Overview
- [x] Customer Growth & Retention module
- [x] Data Reliability Center
- [x] Market & Demand Intelligence
- [x] Restaurant & Cuisine Opportunity
- [x] Decision Lab and configurable opportunity score
- [x] Aggregate-only CSV and decision-brief exports
- [x] Public read-only Streamlit Community Cloud deployment
- [x] Repository cleanup: retired frontend/site code and Node-only tooling removed

## Verified acceptance checks

- [x] 150,281 source rows and 36 columns reconcile
- [x] Date interpretation is explicit: `MM/DD/YYYY`, 0 invalid dates
- [x] 148,668 valid transactions plus 1,613 excluded rows reconcile to the raw source
- [x] ₹986,564,268 gross valid INR sales reconciles
- [x] Repeat customer rate and cohort retention remain separate metrics
- [x] Filters update all metrics and visualisations in the active workspace
- [x] Unsupported operational fields are not fabricated
- [x] Rating and menu coverage remain visible at the point of interpretation
- [x] 822 raw market labels reconcile to cleaned markets plus Unknown
- [x] Market growth uses equal-length comparison windows
- [x] Eligibility thresholds prevent tiny comparison bases from leading rankings
- [x] Market rows expose sample size, mapping coverage and confidence
- [x] Multi-cuisine allocation reconciles exactly to cuisine-covered transactions
- [x] Cuisine and restaurant-name mappings are generated as reviewable CSV artifacts
- [x] Opportunity rankings enforce minimum current and comparison evidence
- [x] Restaurant evidence is labelled as observed listings rather than durable outlet performance
- [x] Decision Lab recalculates relative scores from explicit demand, growth, reach, gap and quality weights
- [x] Decision Lab preserves minimum evidence thresholds and optional confidence discounting
- [x] Scenario presets, comparison, rank movement and decision-brief export are available for the active session
- [x] Navigation, controls, table selection and export affordances have accessibility coverage
- [x] All six Streamlit workspaces render locally with no raw-record dependency
- [x] Public URL smoke check passes for unauthenticated load, aggregate KPIs and module navigation

## Phase 0 — Data contract and product foundation

- [x] Aggregate version `1.1.0` recorded in `data/analytics.json`
- [x] Source schema requires the audited 36-column contract before regeneration
- [x] `source.rows`, `quality.raw_rows` and valid/excluded transaction totals reconcile
- [x] Raw-denominator missing-rating and missing-menu counts are explicit and tested: 88,755 and 138,145
- [x] Python validators fail loudly on schema/version/reconciliation drift
- [x] Shared eligibility, cohort, lifecycle, reliability and rank-movement helpers are covered by tests
- [x] Raw source remains local and excluded; only derived aggregate/mapping artifacts are regenerated

## Phase 1 — Streamlit shell and shared filters

- [x] Navigation labels and page copy are implemented in the Streamlit shell
- [x] Period and market filters persist in namespaced session state
- [x] Market Demand uses a locked All cleaned markets comparison scope
- [x] Locked Valid INR rule, source window, record count and public read-only boundary are visible
- [x] Reset restores All markets and All years without resetting the active workspace
- [x] Metric dictionary dialog exposes aggregate version, definitions, checksum and evidence boundary
- [x] `DINESCOPE_FEATURE_FLAGS` supports all-on defaults and comma-separated staged allowlists
- [x] Streamlit AppTest covers navigation, page-aware filters, reset, methodology and staged flags

## Phase 2 — Overview and Customer Growth

- [x] Overview exposes five audited KPIs with definitions and exact Indian-format values
- [x] Overview includes a 33-point Transactions/Sales Altair toggle with monthly tooltips
- [x] Overview includes the decision brief, top-five source-market footprint, lifecycle table and reliability hand-off
- [x] Customer Growth exposes Active, New, Repeat, Repeat rate and Transactions/customer KPIs
- [x] Customer Growth includes acquisition-versus-return trend, frequency depth, cohort retention and lifecycle summary
- [x] Customer Growth includes the seven-row segment evidence/action table and aggregate CSV export
- [x] Chart/table builders preserve default and filtered source values in pure tests

## Phase 3 — Reliability and Market Demand

- [x] Data Reliability mirrors the five reference quality KPIs
- [x] Transaction reconciliation makes raw − excluded = valid visible alongside the locked INR validity rule
- [x] Full source fingerprint, date format, aggregate version, mapping counts and SHA-256 checksum are exposed
- [x] The issue register uses raw-row denominators for zero sales, missing sales, unsupported currency, missing rating and missing menu attributes
- [x] Market Demand applies current/comparison eligibility at the selected threshold
- [x] Market Demand includes the scale × momentum quadrant, selected-market brief, monthly pulse, rank controls and eligible-only CSV export
- [x] Default eligibility and reliability values are covered by AppTest and pure tests

## Phase 4 — Cuisine Opportunity and restaurant evidence

- [x] Cuisine Opportunity mirrors canonical cuisines, highest observed demand, eligible opportunities, top signal and field coverage
- [x] Proportional `1/n` multi-cuisine allocation is visible in the leading-demand chart, heatmap, selected brief and reconciliation note
- [x] Evidence thresholds enforce current and comparison allocated-transaction minimums
- [x] Selected diagnostics expose signal, growth, reach, observed listings, demand-to-listing index and rating/menu coverage
- [x] Eligible opportunity ranking supports opportunity, demand, growth and demand/listing sorting plus aggregate-only CSV export
- [x] Restaurant identity audit exposes raw/normalized/repeated name counts and repeated IDs without claiming outlet performance
- [x] Default all-years and 2020 KPI/table values are covered by pure helper tests and Streamlit AppTest

## Phase 5 — Decision Lab

- [x] Decision Lab uses the same allocation, evidence threshold and confidence factors as Cuisine Opportunity
- [x] Five adjustable evidence weights normalize to 100% and expose the active formula and confidence discount state
- [x] Session-only scenario library supports naming, saving, loading, comparison selection and removal
- [x] Comparison view shows current versus saved leader, score, leader stability and diagnostic explanation
- [x] Ranked investigation queue exposes baseline rank, signed movement and the top 25 rows while export retains the full queue
- [x] Decision brief export remains aggregate-only and includes scope, threshold, confidence setting and weight metadata
- [x] Default balanced ranking and demand-led movement are covered by pure scoring tests and Streamlit AppTest

## UI hardening and cleanup record

- [x] Added a light-on-evergreen DineScope lockup and icon for Streamlit sidebar/logo surfaces
- [x] Replaced invalid percentage formats with supported Streamlit formats
- [x] Added reversible Chart/Data table controls to analytical charts
- [x] Rebuilt Leading cuisine demand with a validated horizontal bar chart and numeric guardrails
- [x] Documented lifecycle segments as order-based food-delivery customer cohorts
- [x] Added responsive wrapping, readable metric values, table column widths and sidebar button contrast
- [x] Kept Metric dictionary access in the sidebar and aligned metric help controls with wrapped labels
- [x] Added responsive top spacing below Streamlit's mobile toolbar
- [x] Moved the aggregate from the retired frontend directory to `data/analytics.json`
- [x] Removed retired React/Next/Vite/Cloudflare/Sites source, configs and build/test tooling
- [x] Replaced Node-only release and aggregate checks with Python `unittest` coverage
- [x] Updated README, methodology, release and public-boundary docs to describe the Streamlit-only architecture

## Next recommended build sequence

1. Keep aggregate checksum/reconciliation and Streamlit AppTest checks green while the public baseline is monitored.
2. Consider server-backed team sharing for saved Decision Lab scenarios only when durable collaboration becomes a product requirement.
