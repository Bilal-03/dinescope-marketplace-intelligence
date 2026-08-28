# DineScope implementation status

Updated: 28 August 2026

## Current release: Public Streamlit full-parity baseline + optional collaboration backlog

- [x] Phase 0 — Product framing, DineScope brand identity, repository and deployment-ready shell
- [x] Phase 1 — Source audit, schema/date contract, transaction exclusions, checksum and metric definitions
- [x] Phase 2a — Reproducible aggregate pipeline for deployment-safe analytics data
- [x] Phase 3a — Core KPIs, repeat logic, lifecycle segmentation and cohort-retention calculations
- [x] Phase 4 — Responsive design system, global filters, metric dictionary and empty/planned states
- [x] Phase 5a — Executive overview
- [x] Phase 5b — Customer Growth & Retention module
- [x] Phase 5c — Data Reliability Center
- [x] Authentication foundation — optional ChatGPT identity plus server-side Admin/Analyst role resolution
- [x] CSV export — customer segment evidence table
- [x] Phase 2b — Auditable locality-to-metro mapping (restaurant-name mapping remains with the restaurant phase)
- [x] Phase 5d — Market & Demand Intelligence
- [x] Phase 5e — Restaurant & Cuisine Opportunity
- [x] Phase 6 — Decision Lab and configurable opportunity score
- [x] Phase 7 — Expanded interaction/accessibility test coverage and performance budget
- [x] Phase 8a — Portfolio case study, production screenshots and release-readiness package
- [x] Public release decision — owner approved public read-only Streamlit access on 28 August 2026
- [x] Streamlit baseline foundation — six aggregate-only workspaces, exports and DineScope theme
- [x] Streamlit data contract — versioned aggregate, source-schema validation and fail-loud quality reconciliation
- [x] Streamlit Phase 1 — parity shell, page-aware filters, methodology dialog and feature-flag state
- [x] Streamlit Phase 2 — Overview and Customer Growth visual/table parity
- [x] Streamlit Phase 3 — Reliability and Market Demand parity
- [x] Streamlit Phase 4 — Cuisine Opportunity parity and restaurant evidence
- [x] Streamlit Phase 5 — session-only Decision Lab scenarios, comparison and rank movement
- [x] Streamlit local acceptance — dependency install, Python tests and browser-rendered module checks
- [x] Streamlit Community Cloud publication — [public app](https://dinescope-marketplace-intelligence.streamlit.app/) is live from `main` with Python 3.11
- [x] Streamlit UI hardening — high-contrast sidebar brand lockup, responsive metric/table sizing, safe percentage formats, explicit Chart/Data table switches and repaired cuisine demand visual

## Verified acceptance checks

- [x] 150,281 source rows and 36 columns reconcile
- [x] Date interpretation is explicit: `MM/DD/YYYY`, 0 invalid dates
- [x] 148,668 valid transactions plus 1,613 excluded rows reconcile to the raw source
- [x] ₹986,564,268 gross valid INR sales reconciles
- [x] Repeat customer rate and cohort retention remain separate metrics
- [x] Filters update all metrics and visualisations in the active module
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
- [x] Scenario presets, comparison, rank movement and decision-brief export are available
- [x] Navigation, controls, table selection and export affordances have accessibility contract coverage
- [x] Keyboard focus states are visible and selectable market/cuisine rows support Enter/Space
- [x] Performance budgets cover the aggregate payload, client JavaScript and client CSS
- [x] Portfolio case study links evidence boundaries, three representative production captures and a release gate
- [x] Public Streamlit adapter reconciles 148,668 valid transactions to the existing aggregate
- [x] All six Streamlit workspaces render locally with no raw-record dependency
- [x] Public URL smoke check — aggregate KPIs, disclaimer and Cuisine Opportunity navigation verified unauthenticated

## Phase 0 completion record — 28 August 2026

- [x] Aggregate version `1.1.0` recorded in `app/data/analytics.json`
- [x] Source schema requires the audited 36-column contract before regeneration
- [x] `source.rows`, `quality.raw_rows` and valid/excluded transaction totals reconcile
- [x] Raw-denominator missing-rating and missing-menu counts are explicit and tested: 88,755 and 138,145
- [x] Python and TypeScript aggregate validators fail loudly on schema/version/reconciliation drift
- [x] Shared eligibility, cohort, lifecycle, reliability and rank-movement helpers are covered by tests
- [x] Raw source remains local and excluded; only derived aggregate/mapping artifacts are regenerated

## Phase 1 completion record — 28 August 2026

- [x] Reference navigation labels and page copy are mirrored in the Streamlit shell
- [x] Period and market filters persist in namespaced session state
- [x] Market Demand uses a locked All cleaned markets comparison scope and resets market selection on entry
- [x] Locked Valid INR rule, source window, record count and public read-only boundary are visible
- [x] Reset restores All markets and All years without resetting the active page
- [x] Metric dictionary/methodology dialog exposes aggregate version, definitions, checksum and evidence boundary
- [x] `DINESCOPE_FEATURE_FLAGS` supports all-on defaults and comma-separated staged allowlists; the legacy variable remains a compatibility fallback
- [x] AppTest covers navigation, page-aware filters, reset, methodology and staged flags

## Phase 2 completion record — 28 August 2026

- [x] Overview exposes five reference KPIs with definitions and exact Indian-format values
- [x] Overview includes a 33-point Transactions/Sales Altair toggle with monthly tooltips
- [x] Overview includes the decision brief, top-five source-market footprint, lifecycle table and reliability CTA
- [x] Customer Growth exposes Active, New, Repeat, Repeat rate and Transactions/customer KPIs
- [x] Customer Growth includes acquisition-versus-return stacked data, frequency depth, cohort retention with Cohort/Size/M0–M6 and lifecycle summary
- [x] Customer Growth includes the seven-row segment evidence/action table and aggregate CSV export
- [x] Phase 2 chart/table builders preserve default and filtered source values in pure tests

## Phase 3 completion record — 28 August 2026

- [x] Data Reliability now mirrors the five reference KPIs: valid transaction rate, rating coverage, menu coverage, restaurant match and schema integrity
- [x] Transaction reconciliation makes the exact raw − excluded = valid relationship visible alongside the locked INR validity rule
- [x] Full source fingerprint, date format, aggregate version, mapping counts and SHA-256 checksum are exposed in the public UI
- [x] The five-row issue register uses raw-row denominators for zero sales, missing sales, unsupported currency, missing rating and missing menu attributes
- [x] Market Demand applies the current/comparison eligibility rule at the selected threshold and keeps the comparison surface scoped to all cleaned markets
- [x] Market Demand includes five reference KPIs, scale × momentum quadrant, selectable market brief, monthly transaction pulse, rank controls and eligible-only CSV export
- [x] Market ranking and monthly pulse helpers preserve exact aggregate values; default 19-market eligibility and reliability values are covered by AppTest and pure tests

## Phase 4 completion record — 28 August 2026

- [x] Cuisine Opportunity mirrors the five reference KPIs: canonical cuisines, highest observed demand, eligible opportunities, top opportunity signal and cuisine field coverage
- [x] Proportional `1/n` multi-cuisine allocation is visible in the leading-demand chart, heatmap, selected brief and reconciliation note
- [x] Evidence thresholds enforce current and comparison allocated-transaction minimums with an explicit threshold control
- [x] Selected cuisine-market diagnostics expose signal, growth, reach, observed normalized listings, demand-to-listing index and rating/menu coverage
- [x] Eligible opportunity ranking supports opportunity, demand, growth and demand/listing sorting plus aggregate-only CSV export
- [x] Restaurant identity audit exposes raw/normalized/repeated name counts, repeated IDs and the seven most-observed normalized names without claiming outlet performance
- [x] Default all-years (80 pairs) and 2020 (34 pairs) KPI/table values are covered by pure helper tests and Streamlit AppTest

## Phase 5 completion record — 28 August 2026

- [x] Decision Lab uses the same 1/n allocation, current/comparison evidence threshold and confidence factors as the reference scoring contract
- [x] Five adjustable evidence weights normalize to 100% and expose the active formula and confidence discount state
- [x] Session-only scenario library supports naming, saving, loading, comparison selection and removal without writing to a server or public data artifact
- [x] Comparison view shows current versus saved leader, score, leader stability and a diagnostic explanation before action
- [x] Ranked investigation queue exposes baseline rank, signed up/down/new movement and the top 25 rows while export retains the full queue and scoring metadata
- [x] Decision brief export remains aggregate-only and includes scope, threshold, confidence setting and active weight metadata
- [x] Default balanced ranking and demand-led movement are covered by pure scoring tests and Streamlit AppTest

## Next recommended build sequence

1. Keep the aggregate checksum/reconciliation tests green while the full-parity Streamlit baseline is monitored.
2. Consider server-backed team sharing for saved Decision Lab scenarios only when durable collaboration becomes a product requirement.

## UI hardening completion record — 28 August 2026

- [x] Added a light-on-evergreen DineScope lockup and icon for Streamlit's sidebar/logo surfaces; the original dark lockup remains available for light backgrounds and README/social assets.
- [x] Replaced invalid `%.1%%`/`.1%` Streamlit column formats with the supported `percent` and `+.1f%` formats, removing the number-format toast while preserving ratio semantics.
- [x] Added a reversible Chart/Data table control to every analytical chart and hid the native one-way `Show data` popover so users always have a visible return path.
- [x] Rebuilt Leading cuisine demand with a validated, branded horizontal bar chart and numeric coercion guardrails so non-empty evidence cannot render as blank bars.
- [x] Documented lifecycle segments as order-based food-delivery customer cohorts, including definitions for recency, frequency, share, repeat rate and suggested actions.
- [x] Added responsive wrapping, readable metric values, table column widths and sidebar button contrast for narrow and expanded layouts.
- [x] Kept Metric dictionary access in the sidebar only and aligned Streamlit metric help controls with wrapped labels on Overview and downstream workspaces.
