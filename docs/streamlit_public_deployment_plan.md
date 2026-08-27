# Streamlit public deployment plan

Updated: 28 August 2026

## Executive decision

The Python/Streamlit application is implemented at `streamlit_app.py` and reads the same audited aggregate as the private React/Vinext reference experience. Public read-only publication was approved by the owner on 28 August 2026 and is live at https://dinescope-marketplace-intelligence.streamlit.app/. Streamlit Phases 0–5 are complete; durable server-backed scenario sharing remains an explicit future capability.

Phase 0 contract status: aggregate version `1.1.0`, audited 36-column source validation, explicit raw-denominator coverage counts, fail-loud Python/TypeScript validation and shared evidence helpers are implemented and tested.

Phase 1 shell status: the Streamlit workspace now mirrors the reference navigation/page copy, persists period and market filters in session state, resets Market Demand to an all-cleaned-market comparison, exposes the locked Valid INR rule and source window, and opens the metric dictionary from the top bar or sidebar. Staged module flags are controlled with `DINESCOPE_FEATURE_FLAGS`; a blank value enables all known flags, while a comma-separated allowlist enables only the named flags.

Phase 2 analytics status: Overview and Customer Growth now use the reference KPI labels and definitions, Altair-backed monthly performance/customer-mix charts with tooltips, a Transactions/Sales toggle, top-five market and decision-boundary panels, lifecycle/action evidence, frequency depth and Cohort/Size/M0–M6 retention tables. `altair==6.2.2` is pinned in `requirements.txt`.

Phase 3 analytics status: Data Reliability now exposes the five reference quality KPIs, exact transaction reconciliation, the locked valid-INR rule, full source fingerprint and raw-denominator issue register. Market Demand now applies the current/comparison evidence rule, exposes the five reference KPIs, interactive scale × momentum quadrant, selected-market diagnostic brief, monthly transaction pulse, rank controls and eligible-only CSV export. The Streamlit tests assert the default 19-market ranking, exact KPI values, reliability counts and checksum.

Phase 4 analytics status: Cuisine Opportunity now exposes canonical taxonomy coverage, proportional 1/n demand allocation, the five reference KPIs, current/comparison evidence thresholds, leading-demand chart, top-market/top-cuisine heatmap, selected opportunity diagnostics, sorted eligible ranking and CSV export. The restaurant identity audit shows raw/normalized/repeated name counts, repeated IDs and the most-observed normalized names while keeping the boundary that observed listings are not durable outlet supply.

Phase 5 analytics status: Decision Lab now exposes adjustable demand, growth, reach, gap and quality weights, normalization to 100%, confidence discounting, evidence guardrails, session-only scenario save/load/remove, comparison leaders, rank movement versus the balanced baseline, top-25 queue display and metadata-rich aggregate-only decision-brief export. It explicitly states that session scenarios are not durable team sharing.

The public Streamlit app should be read-only and evidence-led. It should not introduce raw customer records, new causal claims or a second, inconsistent metric definition.

## Repository and privacy boundary

The public GitHub repository is `Bilal-03/dinescope-marketplace-intelligence`. The current mirror is source-and-documentation first; the data-publication decision is tracked separately in [`docs/public_data_boundary.md`](./public_data_boundary.md).

- The raw `zomato_business_complete.csv` remains local and is excluded by `.gitignore`.
- The deployment-safe aggregate and reviewable mapping CSVs are approved for the public GitHub mirror and Streamlit runtime.
- The public Streamlit release uses the approved aggregate and must never silently fall back to raw source rows.
- The private Sites project configuration is intentionally not copied into the public repository.
- No tokens, `.env` files, private visitor lists or deployment credentials belong in GitHub.
- The README and app footer must continue to state that this is an independent portfolio analysis and is not affiliated with Zomato, Swiggy or another delivery company.

## Recommended implementation sequence

### 1. Add a Streamlit entry point

Create `streamlit_app.py` at the repository root. Keep data loading in a small adapter module so the same metric definitions remain testable outside the UI:

```text
app/data/analytics.json
  → Python adapter and validation
  → Streamlit session state and filters
  → read-only analytics pages
```

Use `st.set_page_config`, a compact sidebar filter surface and a consistent page-level header. Prefer native Streamlit components (`st.metric`, `st.dataframe`, `st.download_button`, `st.tabs`, containers and status messages) before adding another chart framework. Custom CSS can carry the DineScope visual language, but should remain small and tested against narrow widths.

### 2. Preserve metric contracts

Port the current definitions instead of recomputing ad hoc in the UI:

- valid transactions, gross valid INR sales, active customers and average transaction value;
- repeat rate separately from cohort retention;
- equal-length market growth windows with current/comparison sample thresholds;
- equal `1/n` multi-cuisine allocation with additive reconciliation;
- conservative restaurant listing context;
- opportunity score components, confidence discounts and Decision Lab weights.

The adapter should fail loudly when required aggregate keys are missing and expose the source fingerprint, date format and coverage fields in the Data Reliability view.

### 3. Reach module parity in priority order

1. Overview: audited KPIs, monthly momentum and decision brief. **Complete.**
2. Customer Growth: frequency, lifecycle segments, cohort retention and CSV export. **Complete.**
3. Data Reliability: reconciliation, coverage, mappings and limitations. **Complete.**
4. Market Demand: scale, growth, eligibility and confidence. **Complete.**
5. Cuisine Opportunity: taxonomy, additive demand, evidence thresholds and opportunity signals. **Complete.**
6. Decision Lab: weights, confidence discount, comparison and decision-brief export. **Complete.**

The first public cut can launch after Overview, Customer Growth and Data Reliability are complete, provided the app clearly labels the remaining modules as planned. Full parity is preferable before promoting it as the portfolio flagship.

### 4. Define Streamlit state and sharing boundaries

- Use `st.session_state` for filters and temporary scenario edits.
- Keep CSV and decision-brief downloads available without authentication.
- Do not imply that `st.session_state` is durable storage or team sharing.
- Keep server-backed scenario sharing as a separate future phase with explicit authorization, persistence, versioning and audit requirements.

All widget state is namespaced under `pl_`. Phase 1 shell keys include `pl_page`, `pl_market`, `pl_period` and `pl_methodology_open`; Market and Cuisine controls add `pl_market_minimum`, `pl_market_sort`, `pl_selected_market`, `pl_cuisine_minimum`, `pl_cuisine_sort` and `pl_selected_cuisine`; Decision Lab controls add `pl_decision_minimum`, `pl_decision_confidence_discount`, `pl_decision_weight_*`, `pl_decision_scenario_name`, `pl_decision_scenarios` and `pl_decision_comparison_name`. Feature flags currently recognized are `shell_v2`, `overview_v2`, `customers_v2`, `reliability_v2`, `markets_v2`, `cuisines_v2` and `decision_v2`.

### 5. Pin and verify dependencies

Add a Streamlit-specific dependency set to `requirements.txt` (or a clearly documented deployment requirements file) and pin the Streamlit version used in local validation. Develop and deploy with the same Python version. Avoid adding a database or secrets until a feature requires them.

Streamlit Community Cloud uses the GitHub repository as the app source, watches commits for updates and expects dependency declarations such as `requirements.txt`. See the [Community Cloud deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [dependency guidance](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies) and [secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

### 6. Validate before public release

- Run the existing reconciliation suite and add Streamlit adapter tests for every displayed KPI.
- Run a headless Streamlit smoke test for startup, filter changes, downloads and empty states.
- Check the public build at desktop and narrow viewport widths.
- Scan the repository and rendered app for raw customer IDs, addresses, tokens and private Sites metadata.
- Verify that warnings for rating/menu coverage and unsupported operational metrics remain visible.
- Confirm the public app URL, title, favicon and social copy do not imply company affiliation.
- Record the public release decision in `docs/release_readiness.md`.

## Streamlit Community Cloud release steps

1. Sign in to Streamlit Community Cloud with the GitHub account that administers the repository.
2. Create an app from `Bilal-03/dinescope-marketplace-intelligence`, branch `main`, entry point `streamlit_app.py`.
3. Choose a stable public subdomain and a Python version that matches local validation.
4. Confirm `requirements.txt` resolves without unpinned or unnecessary packages.
5. Deploy and inspect logs plus the first-run experience.
6. In app settings, choose **public and searchable** only after the privacy and disclaimer checks pass. **Completed:** the app is public read-only.
7. Add the Streamlit URL to the README and portfolio case study; retain the existing private Sites URL as the React reference until the migration is complete. **Completed:** URL recorded in README, status and release readiness.

Community Cloud supports deploying from public repositories and lets the owner manage public/private sharing in app settings. See [connecting GitHub](https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/connect-your-github-account) and [sharing an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app).

## Success criteria

The Streamlit release is ready when a fresh visitor can:

- understand the source contract and the independent-portfolio disclaimer;
- filter the data by period and market;
- reproduce the headline KPIs and customer-growth view from the audited aggregate;
- inspect reliability warnings before interpreting an opportunity;
- download an evidence table or decision brief;
- use the app without credentials, secrets or raw customer-level data;
- see a clear “directional investigation signal” boundary around opportunity scores.

## Resolved decisions

- Launch with all six implemented modules rather than a reduced first cut.
- Keep the GitHub repository and Streamlit app public read-only.
- Keep Decision Lab scenarios session-scoped for launch; server-backed sharing remains a later collaboration feature.
