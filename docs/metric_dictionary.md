# Metric dictionary

| Metric | Formula | Grain | Limitation |
|---|---|---|---|
| Valid transactions | Distinct valid Order IDs | Filtered transaction | Excludes invalid, non-positive and non-INR rows |
| Gross sales | Sum of valid positive INR Sales Amount | Filtered transaction | Source is public/synthetic and not company financial reporting |
| Average transaction value | Gross sales / valid transactions | Filtered transaction | Source grain may not represent a conventional order basket |
| Active customers | Distinct User IDs with a valid transaction | Filtered customer | Activity exists only inside the observed source window |
| New customers | First observed valid transaction in source-market scope falls in period | Filtered customer | “New” means first observed, not confirmed first-ever platform order |
| Repeat customers | Customers with at least two valid transactions in scope | Filtered customer | Changes when market or period filters change |
| Repeat customer rate | Repeat customers / active customers | Filtered customer | Not equivalent to cohort retention |
| Cohort retention | Active cohort customers at age M / cohort size | Acquisition cohort | Immature cohorts have fewer observable ages |
| Orders per customer | Valid transactions / active customers | Filtered customer | Uses source transaction grain |
| Market transaction growth | (Current comparable-window transactions − previous comparable-window transactions) / previous transactions | Cleaned market | Suppressed when the comparison base has fewer than 50 transactions |
| Market repeat rate | Customers with 2+ transactions / market active customers | Cleaned market and window | Low rates partly reflect sparse source observations |
| Market concentration | Transactions in five largest cleaned markets / current-window transactions | Comparable market window | Unknown locations remain outside named-market rankings |
| Market confidence | Rule using sample size and high-confidence mapping share | Cleaned market | Confidence describes evidence strength, not future certainty |
