# Release readiness

Updated: 27 August 2026  
Product: PlateLens — Food Delivery Marketplace Intelligence

## Decision summary

| Release surface | Status | Decision |
| --- | --- | --- |
| Private production workspace | **Ready** | Keep the current owner-only deployment available for review. |
| Portfolio case-study package | **Ready** | Case study, screenshots and evidence boundaries are checked into the repository. |
| Public unauthenticated deployment | **Pending owner approval** | Do not change site access until the owner explicitly chooses public release. |

This document is a release gate, not an instruction to publish. Public access would be a meaningful external-state change and requires an explicit owner decision after the checks below are complete.

## Readiness checklist

### Product and narrative

- [x] Product scope is clear: Product/Growth first, with Marketplace, Category and City Operations workflows.
- [x] The portfolio narrative distinguishes observed evidence, assumptions and hypotheses.
- [x] Unsupported operational metrics are called out instead of being implied by the UI.
- [x] Screenshots represent the live product surface and avoid raw customer-level records.
- [ ] Owner has approved the final public portfolio wording and whether the product should be linked publicly.

### Data and trust

- [x] Source contract, checksum, date interpretation and validity rule are documented.
- [x] Valid rows and excluded rows reconcile to the raw source.
- [x] Gross sales, customer counts, repeat rate and coverage metrics reconcile to the aggregate.
- [x] Market, cuisine and restaurant mappings are reviewable CSV artifacts.
- [x] Minimum evidence thresholds and confidence labels are visible in the product.
- [x] Raw customer-level records and addresses are excluded from the browser payload.
- [ ] Before public release, perform a final privacy review of screenshots, logs and any future support exports.

### Engineering and experience

- [x] Automated analytics and interface-contract tests pass.
- [x] Lint and production build pass.
- [x] Performance budgets pass for aggregate, JavaScript and CSS bundles.
- [x] Keyboard focus, named controls, table-row selection and export affordances have contract coverage.
- [x] Local previews have an explicit auth fallback and role resolution path.
- [ ] If the product is opened publicly, re-run unauthenticated access, deep-link, mobile-width and cache checks against the public URL.

### Deployment and ownership

- [x] Production deployment is private and owner-controlled.
- [x] The repository includes the deployment configuration and repeatable build commands.
- [x] The product states that it is an independent portfolio case study and is not affiliated with a food-delivery company.
- [ ] Public access policy is not yet selected: owner-only, invite-only or public read-only.
- [ ] If public, confirm that the social preview and favicon do not imply an unauthorised affiliation.
- [ ] If public, add a visible portfolio disclaimer and a support/contact path that does not expose private credentials.

## Public-release decision record

Complete this section only when the owner is ready to make the access decision.

```text
Decision:       [ ] Keep private   [ ] Invite-only   [ ] Public read-only
Approved by:    ______________________________
Date:           ______________________________
Notes:          ______________________________
```

Until this record is completed, the recommended action is to keep the current private deployment unchanged and use the case-study package for review.

## Next build after release decision

The next product capability after a release decision is server-backed team sharing for saved Decision Lab scenarios. Local presets are deliberately device-scoped today; durable collaboration needs an explicit persistence model, authorization policy and audit trail.

