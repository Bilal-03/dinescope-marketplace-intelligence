# Streamlit public deployment plan

Updated: 27 August 2026

## Executive decision

The current PlateLens experience is a React/Vinext application hosted privately on Sites. Streamlit Community Cloud runs Python entry points, so the current frontend cannot be deployed there unchanged. The recommended path is a **Python/Streamlit parity application** that reads the same audited aggregate and preserves the existing React app as the richer private reference implementation during the migration.

The public Streamlit app should be read-only and evidence-led. It should not introduce raw customer records, new causal claims or a second, inconsistent metric definition.

## Repository and privacy boundary

The public GitHub repository is `Bilal-03/platelens-food-delivery-intelligence`. The current mirror is source-and-documentation first; the data-publication decision is tracked separately in [`docs/public_data_boundary.md`](./public_data_boundary.md).

- The raw `zomato_business_complete.csv` remains local and is excluded by `.gitignore`.
- The deployment-safe aggregate and reviewable mapping CSVs are kept out of the public GitHub mirror for now. They contain derived commercial and customer-behavior metrics, so publishing them requires explicit data-publication approval and a final privacy review.
- The public Streamlit release must use either an approved aggregate, a redacted aggregate or a synthetic fixture; it must not silently fall back to raw source rows.
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

Use `st.set_page_config`, a compact sidebar filter surface and a consistent page-level header. Prefer native Streamlit components (`st.metric`, `st.dataframe`, `st.download_button`, `st.tabs`, containers and status messages) before adding another chart framework. Custom CSS can carry the PlateLens visual language, but should remain small and tested against narrow widths.

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

1. Overview: audited KPIs, monthly momentum and decision brief.
2. Customer Growth: frequency, lifecycle segments, cohort retention and CSV export.
3. Data Reliability: reconciliation, coverage, mappings and limitations.
4. Market Demand: scale, growth, eligibility and confidence.
5. Cuisine Opportunity: taxonomy, additive demand, evidence thresholds and opportunity signals.
6. Decision Lab: weights, confidence discount, comparison and decision-brief export.

The first public cut can launch after Overview, Customer Growth and Data Reliability are complete, provided the app clearly labels the remaining modules as planned. Full parity is preferable before promoting it as the portfolio flagship.

### 4. Define Streamlit state and sharing boundaries

- Use `st.session_state` for filters and temporary scenario edits.
- Keep CSV and decision-brief downloads available without authentication.
- Do not imply that `st.session_state` is durable storage or team sharing.
- Keep server-backed scenario sharing as a separate future phase with explicit authorization, persistence, versioning and audit requirements.

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
2. Create an app from `Bilal-03/platelens-food-delivery-intelligence`, branch `main`, entry point `streamlit_app.py`.
3. Choose a stable public subdomain and a Python version that matches local validation.
4. Confirm `requirements.txt` resolves without unpinned or unnecessary packages.
5. Deploy and inspect logs plus the first-run experience.
6. In app settings, choose **public and searchable** only after the privacy and disclaimer checks pass.
7. Add the Streamlit URL to the README and portfolio case study; retain the existing private Sites URL as the React reference until the migration is complete.

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

## Open decisions

- Whether the public Streamlit app should launch with full module parity or an intentionally smaller first cut.
- Whether the GitHub repository should remain public (recommended for a portfolio/public app) or be made private with additional Streamlit access configuration.
- Whether server-backed Decision Lab sharing is needed after public launch.

