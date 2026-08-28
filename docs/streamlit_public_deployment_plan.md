# Streamlit public deployment plan

Updated: 28 August 2026

## Executive decision

DineScope is now a Streamlit-only product. The public application is implemented at `streamlit_app.py`, reads the audited aggregate at `data/analytics.json`, and is live at https://dinescope-marketplace-intelligence.streamlit.app/. Streamlit Phases 0–5 are complete; durable server-backed scenario sharing remains an explicit future capability.

The repository deliberately contains one canonical runtime and one dependency manifest (`requirements.txt`). Retired frontend/site code, authentication hooks and Node build tooling have been removed so the folder structure matches the deployed product.

## Implemented product foundation

- Aggregate contract version `1.1.0` with audited 36-column source validation.
- Explicit valid-INR transaction rule, raw-denominator quality counts and checksum metadata.
- Deterministic location, cuisine and conservative restaurant-name mappings.
- Pure Python analytics adapter in `streamlit_lib.py` with fail-loud contract validation.
- Responsive Streamlit shell with global period/market filters, public-data boundary and metric dictionary.
- Six connected workspaces: Overview, Customer growth, Market demand, Cuisine gaps, Data reliability and Decision Lab.
- Aggregate-only CSV and decision-brief downloads; no raw customer/order records are loaded or downloadable.

## Architecture

```text
Local source CSV (ignored)
  → scripts/audit_source.py
  → scripts/build_analytics.py
  → data/analytics.json + data/mappings/*.csv
  → streamlit_lib.py validation and metric frames
  → streamlit_app.py workspaces
  → Streamlit Community Cloud
```

The source CSV remains local. The checked-in aggregate carries only derived metrics, reviewable mappings, definitions and quality metadata required by the public app.

## Metric and evidence contracts

The adapter preserves the product definitions instead of recomputing ad hoc in the UI:

- valid transactions, gross valid INR sales, active customers and average transaction value;
- repeat rate separately from cohort retention;
- equal-length market growth windows with current/comparison sample thresholds;
- equal `1/n` multi-cuisine allocation with additive reconciliation;
- conservative restaurant listing context;
- opportunity score components, confidence discounts and Decision Lab weights.

The Data reliability workspace exposes the source fingerprint, date format, validity rule, coverage fields, mapping counts and issue treatment before a user interprets an opportunity.

## Workspace rollout

1. **Overview:** audited KPIs, monthly momentum and decision brief — complete.
2. **Customer growth:** frequency, lifecycle segments, cohort retention and CSV export — complete.
3. **Data reliability:** reconciliation, coverage, mappings and limitations — complete.
4. **Market demand:** scale, growth, eligibility and confidence — complete.
5. **Cuisine opportunity:** taxonomy, additive demand, evidence thresholds and opportunity signals — complete.
6. **Decision Lab:** weights, confidence discount, comparison and decision-brief export — complete.

## State and sharing boundary

- `st.session_state` stores filters and temporary scenario edits.
- CSV and decision-brief downloads are available without authentication.
- Session state is not durable storage or team sharing.
- Server-backed scenario sharing remains a separate future phase requiring authorization, persistence, versioning and an audit trail.

Widget state is namespaced under `pl_`. Feature flags are controlled with `DINESCOPE_FEATURE_FLAGS`; a blank value enables all known workspaces, while a comma-separated allowlist enables only named modules during validation.

## Validation before release

Run the complete Python suite and syntax checks:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python -m py_compile streamlit_app.py streamlit_lib.py
git diff --check
```

Release checks cover aggregate reconciliation, displayed KPI values, filters, workspace rendering, exports, Decision Lab scoring, evidence boundaries and representative screenshots. After a push to `main`, smoke-test the public URL at desktop and narrow viewport widths.

## Streamlit Community Cloud release steps

1. Connect the GitHub account that administers `Bilal-03/dinescope-marketplace-intelligence`.
2. Configure branch `main` and entry point `streamlit_app.py`.
3. Use Python 3.11 and install the pinned `requirements.txt` dependencies.
4. Confirm the app starts without raw-data fallback and the public disclaimer is visible.
5. Review logs and the first-run experience, then keep the app public read-only.

Community Cloud deployment guidance is available in the [official deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [dependency guidance](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies) and [secrets management guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## Success criteria

A fresh visitor can:

- understand the source contract and independent-portfolio disclaimer;
- filter by period and market;
- reproduce headline KPIs and customer-growth views from the audited aggregate;
- inspect reliability warnings before interpreting an opportunity;
- download an aggregate evidence table or decision brief;
- use the app without credentials, secrets or raw customer-level data;
- see a clear directional-investigation boundary around opportunity scores.

## Resolved decisions

- Launch with all six implemented workspaces.
- Keep the GitHub repository and Streamlit app public read-only.
- Keep Decision Lab scenarios session-scoped for launch; server-backed sharing remains a later collaboration feature.
