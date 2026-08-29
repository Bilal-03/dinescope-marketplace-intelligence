# Metric dictionary

| Metric | Formula | Grain | Limitation |
|---|---|---|---|
| Source-valid transactions | Distinct source-valid Order IDs before plausibility filtering | Raw source transaction | Excludes missing IDs/dates, invalid sales flags, non-positive sales and non-INR rows |
| Included analytical transactions | Source-valid Order IDs with positive `Order Value ≤ ₹7,500` | Cleaned transaction | Excludes extreme upper-tail values from all project analytics; source rows remain audited locally |
| Filtered sales | Sum of positive INR Sales Amount for included analytical transactions | Cleaned transaction | Source is public/synthetic and not company financial reporting; source-valid sales remain audit-only |
| Average order value | Filtered sales / included analytical transactions | Cleaned transaction | Plausibility-filtered mean; source grain may not represent a conventional order basket |
| Median order value | Median `Order Value` among included analytical transactions | Cleaned transaction | More representative of a typical order in this heavy-tailed source |
| Active customers | Distinct User IDs with an included analytical transaction | Cleaned customer | Activity exists only inside the observed source window and cleaned scope |
| New customers | First observed included analytical transaction in source-market scope falls in period | Cleaned customer | “New” means first observed, not confirmed first-ever platform order |
| Repeat customers | Customers with at least two included analytical transactions in scope | Cleaned customer | Changes when market, period or plausibility scope changes |
| Repeat customer rate | Repeat customers / active customers | Filtered customer | Not equivalent to cohort retention |
| Cohort retention | Active cohort customers at age M / cohort size | Acquisition cohort | Immature cohorts have fewer observable ages |
| Orders per customer | Included analytical transactions / active customers | Cleaned customer | Uses source transaction grain after plausibility filtering |
| Market transaction growth | (Current comparable-window transactions − previous comparable-window transactions) / previous transactions | Cleaned market | Suppressed when the comparison base has fewer than 50 transactions |
| Market repeat rate | Customers with 2+ transactions / market active customers | Cleaned market and window | Low rates partly reflect sparse source observations |
| Market concentration | Transactions in five largest cleaned markets / current-window transactions | Comparable market window | Unknown locations remain outside named-market rankings |
| Market confidence | Rule using sample size and high-confidence mapping share | Cleaned market | Confidence describes evidence strength, not future certainty |
| Allocated cuisine transactions | Sum of `1/n` per included transaction across its `n` unique canonical cuisines | Cuisine or cuisine-market | Assumes listed cuisines contribute equally; only cuisine-covered cleaned rows are represented |
| Allocated cuisine sales | Sum of filtered Sales Amount × `1/n` across canonical cuisines | Cuisine or cuisine-market | Attribution is proportional, not item-level revenue evidence |
| Observed normalized listings | Distinct conservative normalized restaurant names observed for a cuisine-market pair | Cuisine-market and window | Not a durable outlet count; names may represent branches or unrelated restaurants |
| Demand-to-listing index | Pair allocated transactions per observed listing / period median for eligible pairs | Cuisine-market | Relative supply-context proxy, not proof of undersupply |
| Cuisine opportunity signal | Weighted normalized demand, growth, reach, supply-gap and quality components × confidence factor | Eligible cuisine-market pair | Relative investigation priority; sensitive to chosen period and source coverage |
| Decision Lab score | User-weighted percentile dimensions for demand, growth, reach, gap and quality, normalized to 100%, with optional confidence factor | Eligible cuisine-market pair | Relative scenario ranking; changing weights does not change source metrics or prove causality |
| Rank movement | Balanced-baseline rank minus active scenario rank | Eligible cuisine-market pair | Describes prioritization movement within the same filtered evidence set |
