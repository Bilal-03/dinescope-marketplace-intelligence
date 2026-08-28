# Release readiness

Updated: 28 August 2026
Product: DineScope — Food Marketplace Intelligence

## Decision summary

| Release surface | Status | Decision |
| --- | --- | --- |
| Private production workspace | **Ready** | Keep the current owner-only deployment available for review. |
| Portfolio case-study package | **Ready** | Case study, screenshots and evidence boundaries are checked into the repository. |
| Public unauthenticated deployment | **Live** | Aggregate-only Streamlit app is public; raw records/private Sites metadata remain excluded. |

The owner explicitly approved public Streamlit publication on 28 August 2026. This record authorizes the aggregate-only deployment described in `docs/public_data_boundary.md`; it does not authorize publication of raw records, secrets or private Sites metadata.

## Current Streamlit parity gate

The public Streamlit baseline is live and Phases 0–5 are complete: the aggregate contract and shell are hardened, Overview plus Customer Growth match the reference KPI, chart, cohort, lifecycle and export contracts, Reliability plus Market Demand expose the reference trust and eligibility surfaces, Cuisine Opportunity includes proportional demand, heatmap, selected diagnostics and restaurant identity evidence, and Decision Lab includes session-only scenarios, comparison and rank movement. Durable server-backed scenario sharing remains a separate collaboration backlog item.

## Readiness checklist

### Product and narrative

- [x] Product scope is clear: Product/Growth first, with Marketplace, Category and City Operations workflows.
- [x] The portfolio narrative distinguishes observed evidence, assumptions and hypotheses.
- [x] Unsupported operational metrics are called out instead of being implied by the UI.
- [x] Screenshots represent the live product surface and avoid raw customer-level records.
- [x] Owner has approved the public read-only Streamlit release and public repository linkage.

### Data and trust

- [x] Source contract, checksum, date interpretation and validity rule are documented.
- [x] Valid rows and excluded rows reconcile to the raw source.
- [x] Gross sales, customer counts, repeat rate and coverage metrics reconcile to the aggregate.
- [x] Market, cuisine and restaurant mappings are reviewable CSV artifacts.
- [x] Minimum evidence thresholds and confidence labels are visible in the product.
- [x] Raw customer-level records and addresses are excluded from the browser payload.
- [x] Public runtime is aggregate-only; raw customer/order records are not loaded or downloadable.

### Engineering and experience

- [x] Automated analytics and interface-contract tests pass.
- [x] Lint and production build pass.
- [x] Performance budgets pass for aggregate, JavaScript and CSS bundles.
- [x] Keyboard focus, named controls, table-row selection and export affordances have contract coverage.
- [x] Local previews have an explicit auth fallback and role resolution path.
- [x] Public URL smoke check passes for unauthenticated load, aggregate KPI render and module navigation: https://dinescope-marketplace-intelligence.streamlit.app/
- [x] Streamlit UI hardening pass verifies sidebar/logo contrast, responsive metric and table text, safe percentage formats, reversible chart/data controls and non-empty cuisine demand rendering.
- [x] Overview polish keeps Metric dictionary access in the sidebar and aligns metric help icons with wrapped labels.

### Deployment and ownership

- [x] Production deployment is private and owner-controlled.
- [x] The repository includes the deployment configuration and repeatable build commands.
- [x] The product states that it is an independent portfolio case study and is not affiliated with a food-delivery company.
- [x] Public access policy is selected: public read-only.
- [x] DineScope title, original plate-and-scope identity and favicon do not imply company affiliation.
- [x] Streamlit sidebar includes a visible independent-portfolio disclaimer and public repository support path.

## Public-release decision record

Complete this section only when the owner is ready to make the access decision.

```text
Decision:       [ ] Keep private   [ ] Invite-only   [x] Public read-only
Approved by:    Project owner
Date:           28 August 2026
Notes:          Publish the deployment-safe aggregate and required mappings;
                exclude raw records, secrets and private Sites metadata.
```

The existing private React/Sites deployment remains unchanged; the separate public Streamlit surface is live at https://dinescope-marketplace-intelligence.streamlit.app/.

## Next build after release decision

The next optional capability is server-backed team sharing for saved Decision Lab scenarios. Local/session presets are deliberately session-scoped today and require a separate persistence, authorization and audit design before collaboration is enabled.
