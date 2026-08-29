<p align="center">
  <img src="./assets/brand/dinescope-lockup.png" width="430" alt="DineScope — Food Marketplace Intelligence">
</p>

<h1 align="center">DineScope — Food Marketplace Intelligence</h1>

<p align="center"><strong>See demand. Understand customers. Prioritize growth.</strong></p>

<p align="center">
  <a href="https://dinescope-marketplace-intelligence.streamlit.app/"><img src="https://img.shields.io/badge/Live%20app-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Launch the live Streamlit app"></a>
  <a href="https://github.com/Bilal-03/dinescope-marketplace-intelligence"><img src="https://img.shields.io/badge/Release-Public%20read--only-123C36?style=for-the-badge" alt="Public read-only release"></a>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11">
  <img src="https://img.shields.io/badge/Streamlit-1.62.0-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit 1.62.0">
</p>

<p align="center">
  <a href="https://dinescope-marketplace-intelligence.streamlit.app/">Open the public app</a> ·
  <a href="./STATUS.md">Read the implementation status</a> ·
  <a href="./docs/portfolio_case_study.md">Read the portfolio case study</a>
</p>

**DineScope** is a Food Marketplace Intelligence Platform: an interactive decision-intelligence product that helps Product and Growth teams uncover customer, market, restaurant and cuisine opportunities from food-delivery data. It turns a messy marketplace export into a connected workflow for customer behaviour, market demand, cuisine opportunity and data reliability—then makes the evidence boundary visible before a team acts on a ranking.

This is an independent portfolio case study built from a public or synthetic food-delivery dataset. It is not affiliated with, endorsed by, or based on internal data from Zomato, Swiggy or another food-delivery company.

## Recruiter quick read

| | What DineScope demonstrates |
|---|---|
| **Product problem** | Marketplace teams need to decide where to investigate next, but growth, demand, supply and data quality signals rarely share one trustworthy frame. |
| **Primary users** | Product and Growth first; Marketplace, Category and City Operations as adjacent decision partners. |
| **Product outcome** | A decision-ready analytics workspace that separates observed facts, assumptions and hypotheses instead of turning weak evidence into false precision. |
| **My contribution** | Product framing, metric definitions, data-quality contract, reproducible analytics pipeline, UX architecture, Streamlit implementation, testing and public deployment. |
| **Current status** | Six aggregate-only Streamlit workspaces are live from GitHub `main`; the repository contains one canonical Streamlit implementation. |

### Why this is more than a dashboard

- **Decision-led:** every surface answers a product or marketplace question, not just “what can be plotted?”
- **Trust-aware:** validity rules, denominators, comparison windows, coverage and confidence are shown alongside the metric.
- **End-to-end:** the repository includes the data contract, transformation pipeline, Streamlit UI, tests and deployment configuration.
- **Responsible:** rankings are framed as investigation signals; the product does not invent operational metrics the source cannot support.

## Product surface

The public Streamlit app has six connected workspaces:

| Workspace | What a team can do | Key outputs |
|---|---|---|
| **Overview** | Establish the marketplace baseline and identify the next evidence question. | Five audited KPIs, monthly Transactions/Sales toggle, deterministic decision brief, top source markets, lifecycle mix and reliability hand-off. |
| **Customer growth** | Separate acquisition volume, repeat behaviour and actual cohort return. | Active/New/Repeat metrics, acquisition-versus-return trend, transaction frequency, lifecycle segmentation, M0–M6 cohort-retention table and segment evidence CSV. |
| **Market demand** | Compare meaningful market scale and momentum without letting tiny bases lead. | Reviewed metro mapping, equal-length comparison windows, eligibility thresholds, confidence labels, scale × momentum quadrant, monthly pulse, ranked evidence table and CSV. |
| **Cuisine gaps** | Find cuisine-market pairs worth validating while keeping supply evidence conservative. | Canonical taxonomy, additive 1/n cuisine allocation, opportunity score, demand heatmap, selected diagnostics, observed-listing context, evidence thresholds and CSV. |
| **Data reliability** | Check whether a metric deserves to influence a decision. | Raw-versus-source-valid-versus-included reconciliation, analysis retention, rating/menu/restaurant coverage, schema integrity, source fingerprint, checksum and issue treatment register. |
| **Decision Lab** | Make prioritisation trade-offs explicit and compare scenarios. | Demand/growth/reach/gap/quality weights, confidence discounting, evidence guardrails, session-only presets, leader comparison, rank movement and metadata-rich decision brief export. |

## Evidence snapshot

The published aggregate is generated from **150,281 source rows** and an audited **36-column contract**. Headline analytics use a documented plausibility filter on `Order Value`.

| Evidence | Verified value | How DineScope treats it |
|---|---:|---|
| Source-valid transactions | **148,668** | Distinct orders that pass the source validity rule before plausibility filtering. |
| Source-invalid transactions | **1,613** | Exclusions remain visible and reconcile to the raw denominator; they are not silently dropped. |
| Included analytical transactions | **126,519** | Source-valid orders with `Order Value ≤ ₹7,500`; these power all headline analytics. |
| High-value exclusions | **22,149** | Values above the rounded IQR upper fence remain in the audit but are omitted from project metrics. |
| Filtered sales | **₹139,532,057** | Headline sales from the included analytical scope, not net revenue or company financial reporting. |
| Source-valid sales | **₹986,564,268** | Preserved as an audit baseline; not used as the cleaned headline sales metric. |
| Average order value | **₹1,103** | Filtered sales divided by included analytical transactions; median order value is ₹375. |
| Active customers | **71,947** | Distinct customers with at least one included analytical transaction in the selected scope. |
| Repeat customer rate | **50.2%** | Customers with two or more included analytical transactions; explicitly not cohort retention. |
| Rating coverage | **41.0%** | An evidence-availability measure shown beside interpretation, not a quality score. |
| Menu coverage | **8.1%** | A deliberately visible limitation on menu-based supply comparisons. |
| Raw market labels | **822** | Locality labels are mapped to reviewed metro labels with Unknown retained. |
| Cuisine coverage | **98.9%** | Multi-cuisine demand is allocated proportionally so covered demand remains additive. |
| Repeated restaurant IDs | **123 of 148,541** | Restaurant evidence is presented as observed listings, not durable outlet performance. |

The observed source window is **4 October 2023 through 26 June 2026**. Dates are parsed as `MM/DD/YYYY`; duplicate order IDs and invalid dates are zero in the audited source.

## Product decisions and trade-offs

### Repeat behaviour is not retention

Repeat rate answers “what share of active customers ordered at least twice in this scope?” Cohort retention answers “what share of a first-observed cohort returned at month age *m*?” DineScope keeps both visible so a large repeat number cannot be presented as proof that acquisition is compounding.

### Evidence thresholds come before opportunity rankings

Market growth uses equal-length current and comparison windows with minimum samples. Cuisine-market opportunities require at least 100 allocated current transactions and 50 allocated comparison transactions by default. Smaller bases remain explorable, but they cannot lead the default evidence queue.

### Multi-cuisine demand is additive by design

If an included transaction lists *n* unique canonical cuisines, each cuisine receives an equal `1/n` share of the transaction and filtered sales value. Allocated demand therefore reconciles exactly to cuisine-covered included transactions. This is a directional planning assumption, not item-level revenue attribution.

### Restaurant identity is deliberately conservative

Normalization standardizes accents, case, punctuation and ampersands without fuzzy matching or stripping outlet locations. Because restaurant IDs rarely repeat, the product reports observed normalized listings and coverage context rather than claiming restaurant-level performance.

### Unsupported operations metrics stay out of scope

The source has no delivery-time, cancellation, discount, commission, funnel or campaign fields. DineScope does not fabricate those measures; a new source contract would be required before adding them.

## Technical architecture

```text
Local source CSV (never committed)
        │
        ▼
Python schema gate + source-validity audit + plausibility filter + deterministic mappings
        │
        ▼
Deployment-safe aggregate JSON + mapping CSVs
        │
        ▼
Streamlit adapter + session state + native tables/charts
        │
        ▼
Public Streamlit Community Cloud app
```

The Streamlit runtime reads only `data/analytics.json`. It does not query, ship or provide downloads of raw customer/order records. Reviewable location, cuisine and conservative restaurant-name mappings are committed separately so normalization decisions can be inspected.

## Tech stack

| Layer | Technology | Purpose |
|---|---|---|
| Application | **Python 3.11, Streamlit 1.62.0** | Public read-only analytics experience and deployment entry point (`streamlit_app.py`). |
| Analytics | **pandas 2.2.3, NumPy 2.2.6, Altair 6.2.2** | Deterministic frames, scoring helpers, tables and interactive charts. |
| Data pipeline | **Python standard library + pandas** | Source validation, validity rules, mappings, aggregates and checksums. |
| Test tooling | **Python `unittest` + Streamlit AppTest** | Analytics contracts, rendered workspace checks and release-package checks. |
| Hosting | **Streamlit Community Cloud + GitHub `main`** | Public aggregate-only deployment with pinned Python dependencies. |

## Run locally

Create the same Python environment used by Streamlit Community Cloud:

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run streamlit_app.py
```

Open the local URL printed by Streamlit. The app defaults to all known feature flags. To stage a subset during validation:

```bash
DINESCOPE_FEATURE_FLAGS=shell_v2,markets_v2 .venv/bin/streamlit run streamlit_app.py
```

### Rebuild the audited aggregate locally

The raw CSV is intentionally local and ignored by Git. Mapping outputs are written to `data/mappings/`; the cleaned source and exclusion audit are written to `data/cleaned/` and remain ignored by Git.

```bash
.venv/bin/python scripts/audit_source.py /path/to/zomato_business_complete.csv
.venv/bin/python scripts/build_analytics.py /path/to/zomato_business_complete.csv data/analytics.json
```

The builder fails before processing when required fields are missing or the source does not match the audited schema. It writes `data/cleaned/zomato_business_complete_cleaned.csv` and `data/cleaned/zomato_business_complete_exclusion_audit.csv` by default without modifying the raw source. Never place the raw CSV, cleaned row-level extracts or secrets in the public repository.

## Verification and quality gates

Run the complete Python suite before pushing:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python -m py_compile streamlit_app.py streamlit_lib.py
git diff --check
```

The tests cover the aggregate contract, reconciliation, mappings, KPI parity, all six workspaces, filters, exports, Decision Lab scoring, release documentation and representative screenshots. The public URL is smoke-tested after deployment for unauthenticated loading and module navigation.

## Deployment and public-data boundary

- **Repository:** [Bilal-03/dinescope-marketplace-intelligence](https://github.com/Bilal-03/dinescope-marketplace-intelligence)
- **Branch:** `main`
- **Streamlit entry point:** `streamlit_app.py`
- **Runtime:** Python 3.11 with dependencies pinned in `requirements.txt`
- **Visibility:** Public and read-only; the runtime is aggregate-only.
- **Release flow:** push to `main` → Streamlit Community Cloud pulls the repository → the app rebuilds from the pinned requirements.

Public artifacts are limited to:

- `data/analytics.json` — derived aggregate contract v1.3.0 with source-valid and plausibility-filter audit metadata.
- `data/mappings/*.csv` — reviewable location, cuisine and restaurant-name mappings.
- `assets/brand/*` — DineScope logo, icon, favicon and social assets used by the Streamlit app and README.
- `docs/screenshots/*` — aggregate-only product captures.

The raw source CSV, customer/order records, `.streamlit/secrets.toml`, credentials, tokens and private hosting metadata are excluded. See [docs/public_data_boundary.md](./docs/public_data_boundary.md) and [docs/release_readiness.md](./docs/release_readiness.md) for the recorded release gate.

## Five-minute portfolio walkthrough

1. Open the [live Streamlit app](https://dinescope-marketplace-intelligence.streamlit.app/).
2. Start in **Overview** to see the audited KPI baseline and deterministic decision brief.
3. Open **Customer growth** to inspect acquisition-versus-return behaviour and M0–M6 cohort retention.
4. Open **Market demand** or **Cuisine gaps** to see evidence thresholds, confidence and mapping context beside opportunity signals.
5. Open **Decision Lab** to change the five weights, compare the leader and inspect rank movement.
6. Open **Metric dictionary** or **Data reliability** to see how the source contract limits interpretation.

Representative captures are available in [docs/screenshots/](./docs/screenshots/). They demonstrate the product surfaces and evidence treatment without exposing raw customer records.

## Repository map

```text
streamlit_app.py                 Public Streamlit application and workspace rendering
streamlit_lib.py                 Pure metric, eligibility and Decision Lab helpers
data/analytics.json              Audited deployment-safe aggregate
data/mappings/                   Reviewable location, cuisine and restaurant mappings
assets/brand/                    DineScope logo, icon, favicon and social assets
scripts/audit_source.py          Read-only source profiling
scripts/build_analytics.py       Reproducible aggregate + mapping builder
scripts/generate_brand_assets.py Deterministic brand asset generator
tests/                           Python analytics, AppTest and release-package checks
docs/methodology.md              Definitions, assumptions and evidence boundaries
docs/metric_dictionary.md        Metric formulas, grain and limitations
docs/release_readiness.md        Public-release decision and acceptance gate
docs/streamlit_public_deployment_plan.md
                                  Streamlit implementation and rollout record
STATUS.md                         Phase checklist and cleanup status
```

## Roadmap and explicit non-goals

The public baseline is complete through Streamlit Phases 0–5. The next optional capability is **server-backed team sharing for saved Decision Lab scenarios**. It is deliberately not enabled yet because durable collaboration needs a persistence model, authorization policy, versioning and audit trail.

The following remain intentionally out of scope until a stronger source is available:

- causal lift, forecasts, profitability or incremental-market claims;
- delivery operations, cancellation, discount, commission, funnel or campaign analytics;
- durable restaurant-level performance when restaurant IDs rarely repeat;
- demographic targeting recommendations from descriptive source fields.

## Further reading

- [STATUS.md](./STATUS.md) — phase-by-phase implementation checklist and cleanup record.
- [docs/portfolio_case_study.md](./docs/portfolio_case_study.md) — product narrative and portfolio framing.
- [docs/methodology.md](./docs/methodology.md) — source contract, formulas and assumptions.
- [docs/metric_dictionary.md](./docs/metric_dictionary.md) — metric definitions by grain and limitation.
- [docs/release_readiness.md](./docs/release_readiness.md) — deployment and public-release gate.
- [docs/public_data_boundary.md](./docs/public_data_boundary.md) — approved public artifacts and exclusions.
- [docs/streamlit_public_deployment_plan.md](./docs/streamlit_public_deployment_plan.md) — Streamlit parity and rollout plan.

---

**DineScope in one sentence:** a deployment-ready marketplace intelligence product that makes customer growth, demand opportunity and data reliability legible in one workflow—without pretending the data proves more than it does.
