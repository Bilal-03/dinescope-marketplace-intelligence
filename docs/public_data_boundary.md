# Public data boundary

Updated: 27 August 2026

## Current decision

The GitHub repository is public, but the detailed analytics payload is intentionally not copied into it yet. The private Sites application can continue using its deployment-safe aggregate locally and in its existing private deployment.

The following artifacts stay out of the public repository until the owner explicitly approves publication after a privacy review:

- `app/data/analytics.json` — detailed market, customer-behavior and opportunity aggregates.
- `data/mappings/*.csv` — reviewable location, cuisine and restaurant-name mappings.
- `docs/screenshots/*` — captures that display derived commercial metrics.
- `.openai/hosting.json` — private Sites project metadata.

The raw source CSV is excluded independently by `.gitignore` and should never be committed.

## What the public repository contains

The source code, tests, methodology, metric dictionary, portfolio narrative and Streamlit deployment plan are safe to review without publishing the detailed payload. A fresh Streamlit deployment still needs an approved aggregate, redacted aggregate or synthetic fixture before it can render the full analytics workspace.

## Approval needed to complete the data-backed public app

Before adding the detailed aggregate or any equivalent fixture to the public repository, record an explicit decision that confirms:

```text
I approve publishing the selected analytics artifact(s) to the public
GitHub repository and using them in a public Streamlit app after the
privacy scan and disclaimer checks pass.

Approved by: ____________________    Date: ____________________
Scope:       ____________________
```

If the decision is not to publish the detailed payload, use a redacted or synthetic data artifact and label the public app accordingly.

