"""Pure analytics helpers shared by the public Streamlit interface and tests."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

import pandas as pd


DATA_PATH = Path(__file__).parent / "app" / "data" / "analytics.json"
AGGREGATE_VERSION = "1.1.0"
DEFAULT_WEIGHTS = {"demand": 25, "growth": 25, "reach": 20, "gap": 15, "quality": 15}
DECISION_DIMENSIONS = ("demand", "growth", "reach", "gap", "quality")
CONFIDENCE_FACTORS = {"High": 1.0, "Medium": 0.85, "Low": 0.65}
FEATURE_FLAG_NAMES = (
    "shell_v2",
    "overview_v2",
    "customers_v2",
    "reliability_v2",
    "markets_v2",
    "cuisines_v2",
    "decision_v2",
)
REQUIRED_TOP_LEVEL_KEYS = {
    "aggregate_version",
    "source",
    "quality",
    "filters",
    "market_views",
    "cuisine_views",
    "scopes",
    "definitions",
}
REQUIRED_SOURCE_KEYS = {
    "filename",
    "sha256",
    "rows",
    "columns",
    "expected_columns",
    "schema_matches",
    "date_format",
    "date_min",
    "date_max",
}
REQUIRED_QUALITY_KEYS = {
    "raw_rows",
    "valid_transactions",
    "excluded_transactions",
    "valid_rate",
    "zero_sales",
    "missing_sales",
    "unsupported_currency",
    "missing_rating_rows",
    "missing_menu_attribute_rows",
    "rating_coverage",
    "menu_coverage",
    "restaurant_match_rate",
    "duplicate_order_ids",
    "invalid_dates",
}


def load_analytics(path: Path = DATA_PATH, validate: bool = True) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if validate:
        assert_valid_data_contract(payload)
    return payload


def scope_key(market: str, period: str) -> str:
    return f"{market}|{period}"


def parse_feature_flags(raw: str | None = None) -> dict[str, bool]:
    """Parse a comma-separated feature-flag allowlist for staged Streamlit rollout.

    An unset/blank value enables every known flag for local development and the
    current public baseline. Once a value is supplied, only explicitly listed
    flags are enabled; ``all`` is a convenient explicit allowlist.
    """

    value = os.getenv("PLATELENS_FEATURE_FLAGS", "") if raw is None else raw
    tokens = {token.strip().lower() for token in value.split(",") if token.strip()}
    if not tokens or "all" in tokens:
        return {name: True for name in FEATURE_FLAG_NAMES}
    return {name: name in tokens for name in FEATURE_FLAG_NAMES}


def eligible_market_rows(
    rows: list[dict[str, Any]],
    minimum_orders: int = 200,
    comparison_floor: int = 50,
) -> list[dict[str, Any]]:
    """Return markets that satisfy the comparable-window evidence rule."""

    minimum = max(0, int(minimum_orders))
    comparison_minimum = max(max(0, int(comparison_floor)), minimum / 2)
    return [
        row
        for row in rows
        if row.get("orders", 0) >= minimum
        and row.get("previous_orders", 0) >= comparison_minimum
        and row.get("growth_orders") is not None
    ]


def eligible_cuisine_pairs(
    pairs: list[dict[str, Any]],
    minimum_orders: int = 100,
    comparison_floor: int = 25,
) -> list[dict[str, Any]]:
    """Return cuisine-market pairs that satisfy current/comparison evidence rules."""

    minimum = max(0, int(minimum_orders))
    comparison_minimum = max(max(0, int(comparison_floor)), minimum / 2)
    return [
        row
        for row in pairs
        if row.get("allocated_orders", 0) >= minimum
        and row.get("previous_allocated_orders", 0) >= comparison_minimum
        and row.get("growth") is not None
    ]


def select_market_rows(rows: list[dict[str, Any]], market: str | None) -> list[dict[str, Any]]:
    """Scope rows without mutating the aggregate or treating a detail selection as a cohort."""

    if not market or market == "All markets":
        return list(rows)
    return [row for row in rows if row.get("market") == market]


def customer_cohort_frame(cohorts: list[dict[str, Any]], months: int = 6) -> pd.DataFrame:
    """Create the parity cohort table with explicit cohort size and M0–M6 columns."""

    month_columns = [f"M{age}" for age in range(months + 1)]
    columns = ["Cohort", "Size", *month_columns]
    records = []
    for cohort in cohorts:
        retention = list(cohort.get("retention", []))
        records.append(
            {
                "Cohort": cohort.get("cohort"),
                "Size": cohort.get("size"),
                **{
                    column: retention[index] if index < len(retention) else None
                    for index, column in enumerate(month_columns)
                },
            }
        )
    return pd.DataFrame(records, columns=columns)


def lifecycle_frame(scope: dict[str, Any]) -> pd.DataFrame:
    """Create the shared lifecycle evidence table used by overview and customer views."""

    columns = [
        "Segment",
        "Customers",
        "Share",
        "Orders / customer",
        "Sales / customer",
        "Repeat rate",
        "Median recency",
        "Suggested action",
    ]
    records = []
    for row in scope.get("segments", []):
        records.append(
            {
                "Segment": row.get("segment"),
                "Customers": row.get("customers"),
                "Share": row.get("customer_share"),
                "Orders / customer": row.get("orders_per_customer"),
                "Sales / customer": row.get("sales_per_customer"),
                "Repeat rate": row.get("repeat_rate"),
                "Median recency": row.get("median_recency"),
                "Suggested action": row.get("action"),
            }
        )
    return pd.DataFrame(records, columns=columns)


def monthly_performance_frame(scope: dict[str, Any], metric: str = "orders") -> pd.DataFrame:
    """Return the selected 33-point Overview series with stable chart columns."""

    if metric not in {"orders", "sales"}:
        raise ValueError("Overview metric must be 'orders' or 'sales'")
    rows = [
        {
            "Month": pd.to_datetime(row["month"]),
            "Value": row[metric],
            "Metric": "Valid transactions" if metric == "orders" else "Gross sales",
        }
        for row in scope.get("monthly", [])
    ]
    return pd.DataFrame(rows, columns=["Month", "Value", "Metric"])


def customer_mix_frame(scope: dict[str, Any]) -> pd.DataFrame:
    """Return new/returning customer counts in tidy form for a stacked chart."""

    rows = []
    for point in scope.get("monthly", []):
        month = pd.to_datetime(point["month"])
        rows.extend(
            [
                {"Month": month, "Customer type": "New customers", "Customers": point["new_customers"]},
                {"Month": month, "Customer type": "Returning customers", "Customers": point["returning_customers"]},
            ]
        )
    return pd.DataFrame(rows, columns=["Month", "Customer type", "Customers"])


def frequency_frame(scope: dict[str, Any]) -> pd.DataFrame:
    """Return frequency counts with human-readable labels for chart tooltips."""

    rows = []
    for point in scope.get("frequency", []):
        frequency = str(point["frequency"])
        rows.append(
            {
                "Frequency": frequency,
                "Label": f"{frequency} transaction" if frequency == "1" else f"{frequency} transactions",
                "Customers": point["customers"],
            }
        )
    return pd.DataFrame(rows, columns=["Frequency", "Label", "Customers"])


def market_summary_frame(data: dict[str, Any], limit: int = 5) -> pd.DataFrame:
    """Return the top source-market footprint used by the Overview evidence panel."""

    rows = []
    for index, row in enumerate(data.get("market_summary", [])[:limit], start=1):
        rows.append(
            {
                "Rank": index,
                "Market": row.get("market"),
                "Transactions": row.get("orders"),
                "Gross sales": row.get("sales"),
                "Repeat rate": row.get("repeat_rate"),
            }
        )
    return pd.DataFrame(rows, columns=["Rank", "Market", "Transactions", "Gross sales", "Repeat rate"])


def market_ranking_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Return the auditable eight-column market ranking used by Market Demand.

    The aggregate keeps calculations in their native units (transaction counts,
    rupees and proportions). Formatting belongs to the Streamlit table so CSV
    exports retain the exact values used by the ranking.
    """

    records = [
        {
            "Market": row.get("market"),
            "Transactions": row.get("orders"),
            "Growth": row.get("growth_orders"),
            "Customers": row.get("customers"),
            "Repeat rate": row.get("repeat_rate"),
            "Avg. txn value": row.get("average_transaction_value"),
            "Txn share": row.get("order_share"),
            "Confidence": row.get("confidence"),
        }
        for row in rows
    ]
    return pd.DataFrame(
        records,
        columns=[
            "Market",
            "Transactions",
            "Growth",
            "Customers",
            "Repeat rate",
            "Avg. txn value",
            "Txn share",
            "Confidence",
        ],
    )


def market_monthly_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Flatten monthly market pulses into a tidy chart/export frame."""

    records = []
    for row in rows:
        for point in row.get("monthly_orders", []):
            records.append(
                {
                    "Market": row.get("market"),
                    "Month": pd.to_datetime(point.get("month")),
                    "Transactions": point.get("orders"),
                }
            )
    return pd.DataFrame(records, columns=["Market", "Month", "Transactions"])


def cuisine_summary_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Return the leading-cuisine demand series with additive allocation fields."""

    records = [
        {
            "Cuisine": row.get("cuisine"),
            "Allocated txns": row.get("allocated_orders"),
            "Allocated sales": row.get("allocated_sales"),
            "Customers": row.get("customers"),
            "Markets": row.get("markets"),
            "Observed listings": row.get("observed_listings"),
        }
        for row in rows
    ]
    return pd.DataFrame(
        records,
        columns=[
            "Cuisine",
            "Allocated txns",
            "Allocated sales",
            "Customers",
            "Markets",
            "Observed listings",
        ],
    )


def cuisine_ranking_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Return the eligible cuisine-market action queue with reference labels."""

    records = [
        {
            "Market · Cuisine": f'{row.get("market")} · {row.get("cuisine")}',
            "Signal": row.get("opportunity_score"),
            "Allocated txns": row.get("allocated_orders"),
            "Growth": row.get("growth"),
            "Customers": row.get("customers"),
            "Listings": row.get("observed_listings"),
            "Demand / listing": row.get("demand_to_listing_index"),
            "Rating cov.": row.get("rating_coverage"),
            "Menu cov.": row.get("menu_coverage"),
            "Confidence": row.get("confidence"),
            "Recommended action": row.get("recommended_action"),
        }
        for row in rows
    ]
    return pd.DataFrame(
        records,
        columns=[
            "Market · Cuisine",
            "Signal",
            "Allocated txns",
            "Growth",
            "Customers",
            "Listings",
            "Demand / listing",
            "Rating cov.",
            "Menu cov.",
            "Confidence",
            "Recommended action",
        ],
    )


def cuisine_heatmap_frame(
    pairs: list[dict[str, Any]], market_limit: int = 7, cuisine_limit: int = 8
) -> pd.DataFrame:
    """Build the top-market/top-cuisine heatmap input without dropping zero cells."""

    market_totals: dict[str, float] = {}
    cuisine_totals: dict[str, float] = {}
    for row in pairs:
        market_totals[row["market"]] = market_totals.get(row["market"], 0) + row.get("allocated_orders", 0)
        cuisine_totals[row["cuisine"]] = cuisine_totals.get(row["cuisine"], 0) + row.get("allocated_orders", 0)
    markets = [name for name, _ in sorted(market_totals.items(), key=lambda item: (-item[1], item[0]))[:market_limit]]
    cuisines = [name for name, _ in sorted(cuisine_totals.items(), key=lambda item: (-item[1], item[0]))[:cuisine_limit]]
    lookup = {(row["market"], row["cuisine"]): row.get("allocated_orders", 0) for row in pairs}
    records = [
        {"Market": market, "Cuisine": cuisine, "Allocated txns": lookup.get((market, cuisine), 0)}
        for market in markets
        for cuisine in cuisines
    ]
    return pd.DataFrame(records, columns=["Market", "Cuisine", "Allocated txns"])


def restaurant_observation_frame(observations: list[dict[str, Any]], limit: int = 7) -> pd.DataFrame:
    """Return conservative normalized-name observations for the identity audit."""

    records = [
        {
            "Normalized name": row.get("normalized_name"),
            "Observed rows": row.get("observed_rows"),
            "Distinct IDs": row.get("distinct_restaurant_ids"),
            "Markets": row.get("markets"),
            "Rating coverage": row.get("rating_coverage"),
            "Menu coverage": row.get("menu_coverage"),
        }
        for row in observations[:limit]
    ]
    return pd.DataFrame(
        records,
        columns=[
            "Normalized name",
            "Observed rows",
            "Distinct IDs",
            "Markets",
            "Rating coverage",
            "Menu coverage",
        ],
    )


def reliability_issue_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the source-level issue register with raw-row denominators."""

    quality = data.get("quality", data)
    return [
        {
            "Issue": "Zero sales",
            "Affected rows": int(quality.get("zero_sales", 0)),
            "Treatment": "Excluded from business KPIs",
            "Severity": "High",
        },
        {
            "Issue": "Missing sales",
            "Affected rows": int(quality.get("missing_sales", 0)),
            "Treatment": "Excluded; preserved in audit totals",
            "Severity": "High",
        },
        {
            "Issue": "Unsupported currency",
            "Affected rows": int(quality.get("unsupported_currency", 0)),
            "Treatment": "USD rows excluded from INR KPIs",
            "Severity": "High",
        },
        {
            "Issue": "Missing rating",
            "Affected rows": int(quality.get("missing_rating_rows", 0)),
            "Treatment": "Coverage shown beside opportunity signals",
            "Severity": "Medium",
        },
        {
            "Issue": "Missing menu attributes",
            "Affected rows": int(quality.get("missing_menu_attribute_rows", 0)),
            "Treatment": "Coverage shown beside opportunity signals",
            "Severity": "Medium",
        },
    ]


def decision_row_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("market", "")), str(row.get("cuisine", ""))


def add_rank_movement(
    rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Add baseline rank and signed movement versus a baseline ranking."""

    baseline = {decision_row_key(row): row.get("rank") for row in baseline_rows}
    output = []
    for row in rows:
        current_rank = row.get("rank")
        baseline_rank = baseline.get(decision_row_key(row))
        delta = baseline_rank - current_rank if baseline_rank is not None and current_rank is not None else None
        output.append({**row, "baseline_rank": baseline_rank, "rank_delta": delta})
    return output


def percentile_score(value: float, values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(candidate <= value for candidate in values) / len(values) * 100


def normalize_weights(weights: dict[str, int | float]) -> dict[str, float]:
    total = sum(weights.values())
    if not total:
        return {"demand": 1.0, "growth": 0.0, "reach": 0.0, "gap": 0.0, "quality": 0.0}
    return {key: value / total for key, value in weights.items()}


def score_decision_pairs(
    pairs: list[dict[str, Any]],
    minimum_orders: int,
    weights: dict[str, int | float],
    confidence_discount: bool = True,
) -> list[dict[str, Any]]:
    comparison_minimum = max(25, minimum_orders / 2)
    eligible = [
        row
        for row in pairs
        if row["allocated_orders"] >= minimum_orders
        and row["previous_allocated_orders"] >= comparison_minimum
        and row["growth"] is not None
    ]
    values = {
        "demand": [row["allocated_orders"] for row in eligible],
        "growth": [row["growth"] for row in eligible],
        "reach": [row["customers"] for row in eligible],
        "gap": [row.get("demand_to_listing_index") or 0 for row in eligible],
        "quality": [(row["rating_coverage"] + row["menu_coverage"]) / 2 for row in eligible],
    }
    normalized = normalize_weights(weights)
    scored: list[dict[str, Any]] = []
    for row in eligible:
        dimensions = {
            "demand": percentile_score(row["allocated_orders"], values["demand"]),
            "growth": percentile_score(row["growth"], values["growth"]),
            "reach": percentile_score(row["customers"], values["reach"]),
            "gap": percentile_score(row.get("demand_to_listing_index") or 0, values["gap"]),
            "quality": percentile_score(
                (row["rating_coverage"] + row["menu_coverage"]) / 2,
                values["quality"],
            ),
        }
        raw_score = sum(dimensions[key] * normalized[key] for key in normalized)
        factor = CONFIDENCE_FACTORS[row["confidence"]] if confidence_discount else 1.0
        scored.append({**row, "dimensions": dimensions, "lab_score": raw_score * factor})
    scored.sort(key=lambda row: (-row["lab_score"], -row["allocated_orders"], row["market"], row["cuisine"]))
    return [{**row, "rank": index} for index, row in enumerate(scored, start=1)]


def decision_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    records = []
    for row in rows:
        dimensions = row["dimensions"]
        movement = row.get("rank_delta")
        movement_label = (
            "New"
            if movement is None
            else f"↑{movement}"
            if movement > 0
            else f"↓{abs(movement)}"
            if movement < 0
            else "—"
        )
        records.append(
            {
                "Rank": row["rank"],
                "Market": row["market"],
                "Cuisine": row["cuisine"],
                "Lab score": round(row["lab_score"], 1),
                "Baseline rank": row.get("baseline_rank"),
                "Move": movement_label,
                "Demand": round(dimensions["demand"]),
                "Growth": round(dimensions["growth"]),
                "Reach": round(dimensions["reach"]),
                "Gap": round(dimensions["gap"]),
                "Quality": round(dimensions["quality"]),
                "Confidence": row["confidence"],
                "Allocated transactions": round(row["allocated_orders"], 1),
                "Transaction growth": row["growth"],
                "Observed listings": row["observed_listings"],
                "Recommended next action": row["recommended_action"],
            }
        )
    return pd.DataFrame(records)


def scenario_summary(scenario: dict[str, Any]) -> str:
    """Compact, human-readable weight summary for the session scenario library."""

    weights = scenario.get("weights", {})
    return (
        f'D{weights.get("demand", 0)} · G{weights.get("growth", 0)} · '
        f'R{weights.get("reach", 0)} · Gap{weights.get("gap", 0)} · Q{weights.get("quality", 0)}'
    )


def rank_movement_label(value: int | None) -> str:
    """Format a rank delta as the reference's up/down/new label."""

    if value is None:
        return "New"
    if value > 0:
        return f"↑{value}"
    if value < 0:
        return f"↓{abs(value)}"
    return "—"


def contract_errors(data: Any) -> list[str]:
    """Return human-readable errors for the deployment-safe aggregate contract."""

    errors: list[str] = []
    if not isinstance(data, dict):
        return ["aggregate must be a JSON object"]

    missing_top_level = sorted(REQUIRED_TOP_LEVEL_KEYS.difference(data))
    if missing_top_level:
        errors.append(f"missing top-level keys: {', '.join(missing_top_level)}")
    if data.get("aggregate_version") != AGGREGATE_VERSION:
        errors.append(
            f"aggregate_version must be {AGGREGATE_VERSION!r}; got {data.get('aggregate_version')!r}"
        )

    source = data.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
    else:
        missing_source = sorted(REQUIRED_SOURCE_KEYS.difference(source))
        if missing_source:
            errors.append(f"missing source keys: {', '.join(missing_source)}")
        if source.get("columns") != source.get("expected_columns"):
            errors.append("source columns do not match expected_columns")
        if source.get("schema_matches") is not True:
            errors.append("source schema_matches must be true")
        sha = source.get("sha256")
        if not isinstance(sha, str) or len(sha) != 64:
            errors.append("source sha256 must be a 64-character string")

    quality = data.get("quality")
    if not isinstance(quality, dict):
        errors.append("quality must be an object")
    else:
        missing_quality = sorted(REQUIRED_QUALITY_KEYS.difference(quality))
        if missing_quality:
            errors.append(f"missing quality keys: {', '.join(missing_quality)}")
        numeric_counts = [
            "raw_rows",
            "valid_transactions",
            "excluded_transactions",
            "zero_sales",
            "missing_sales",
            "unsupported_currency",
            "missing_rating_rows",
            "missing_menu_attribute_rows",
            "duplicate_order_ids",
            "invalid_dates",
        ]
        for key in numeric_counts:
            value = quality.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                errors.append(f"quality.{key} must be a non-negative number")
        raw_rows = quality.get("raw_rows")
        valid_transactions = quality.get("valid_transactions")
        excluded_transactions = quality.get("excluded_transactions")
        if all(isinstance(value, (int, float)) for value in (raw_rows, valid_transactions, excluded_transactions)):
            if valid_transactions > raw_rows:
                errors.append("quality.valid_transactions cannot exceed quality.raw_rows")
            if valid_transactions + excluded_transactions != raw_rows:
                errors.append("quality valid plus excluded transactions must equal raw rows")
            valid_rate = quality.get("valid_rate")
            if not isinstance(valid_rate, (int, float)) or not math.isclose(
                valid_rate, valid_transactions / raw_rows if raw_rows else 0.0, rel_tol=0, abs_tol=1e-12
            ):
                errors.append("quality.valid_rate does not reconcile to valid/raw rows")
        for key in ("rating_coverage", "menu_coverage", "restaurant_match_rate"):
            value = quality.get(key)
            if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                errors.append(f"quality.{key} must be between 0 and 1")
        if isinstance(raw_rows, (int, float)):
            for coverage_key, missing_key in (
                ("rating_coverage", "missing_rating_rows"),
                ("menu_coverage", "missing_menu_attribute_rows"),
            ):
                coverage = quality.get(coverage_key)
                missing = quality.get(missing_key)
                if isinstance(coverage, (int, float)) and isinstance(missing, (int, float)):
                    expected_missing = round(raw_rows * (1 - coverage))
                    if missing != expected_missing:
                        errors.append(f"quality.{missing_key} does not reconcile to raw coverage")

    if isinstance(source, dict) and isinstance(quality, dict):
        if source.get("rows") != quality.get("raw_rows"):
            errors.append("source.rows must equal quality.raw_rows")

    filters = data.get("filters")
    if not isinstance(filters, dict) or not isinstance(filters.get("markets"), list) or not isinstance(filters.get("periods"), list):
        errors.append("filters must contain markets and periods lists")
    for key in ("market_views", "cuisine_views", "scopes", "definitions"):
        if not isinstance(data.get(key), dict):
            errors.append(f"{key} must be an object")
    return errors


def assert_valid_data_contract(data: Any) -> None:
    errors = contract_errors(data)
    if errors:
        raise ValueError("Invalid PlateLens aggregate contract:\n- " + "\n- ".join(errors))


def valid_data_contract(data: dict[str, Any]) -> bool:
    return not contract_errors(data)
