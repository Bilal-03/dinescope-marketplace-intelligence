# Methodology

## Source contract

- Source file: `zomato_business_complete.csv`
- SHA-256: `fc5ca0ca1043e3cfb17ab467a7b87bbcc0a516cd766e962b4850a202d5a88be7`
- Grain used by the product: one source row per unique Order ID
- Date interpretation: explicit `%m/%d/%Y` parsing
- Observed window: 4 October 2017 through 26 June 2020

## Valid transaction rule

A business KPI transaction must have a non-null order ID, a parsed date, a true `Sales Amount Valid` flag, non-null sales greater than zero, and INR currency. Exclusions are preserved in quality aggregates and are never silently deleted.

## Customer definitions

- Active customer: at least one valid transaction in the filtered scope.
- New customer: first observed valid transaction in the filtered source-market scope falls in the selected period.
- Repeat customer: at least two valid transactions in the filtered scope.
- Repeat rate: repeat customers divided by active customers.
- Cohort retention: customers active at cohort age M divided by customers first observed in that cohort month.

RFM-style lifecycle segments use transparent ordering signals only. They do not claim app engagement, customer intent or causal response to a campaign.

## Known limitations

Restaurant IDs rarely repeat, raw city labels mix locality and metro formats, restaurant ratings cover roughly 41% of rows, and menu fields cover roughly 8%. Market ranking and cuisine opportunity modules remain planned until auditable mappings and allocation rules are implemented.
