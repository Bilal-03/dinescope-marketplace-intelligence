#!/usr/bin/env python3
"""Profile the source CSV and emit the audited foundation metrics as JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

try:
    from scripts.data_quality import (
        MAX_ORDER_VALUE_INR,
        PLAUSIBILITY_METHOD,
        PLAUSIBILITY_RULE,
        build_quality_masks,
        plausibility_profile,
    )
except ModuleNotFoundError:  # Direct ``python scripts/audit_source.py`` execution.
    from data_quality import (
        MAX_ORDER_VALUE_INR,
        PLAUSIBILITY_METHOD,
        PLAUSIBILITY_RULE,
        build_quality_masks,
        plausibility_profile,
    )


EXPECTED_COLUMNS = 36


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    frame = pd.read_csv(source, low_memory=False, encoding="utf-8-sig")
    masks = build_quality_masks(frame)
    parsed_dates = masks["order_date"]
    sales = masks["sales"]
    order_value = masks["order_value"]
    quantity = masks["quantity"]
    currency = masks["currency"]
    source_valid = masks["source_valid"]
    analysis_eligible = masks["analysis_eligible"]
    high_value_excluded = masks["high_value_excluded"]
    plausibility_excluded = masks["plausibility_excluded"]

    audited = frame.loc[analysis_eligible, ["Order ID", "User ID"]].copy()
    audited["order_date"] = parsed_dates[analysis_eligible]
    audited["sales"] = sales[analysis_eligible]
    audited["quantity"] = quantity[analysis_eligible]
    customer_orders = audited.groupby("User ID", dropna=False)["Order ID"].nunique()
    repeat_customers = int(customer_orders.ge(2).sum())
    active_customers = int(customer_orders.size)

    monthly = (
        audited.assign(month=audited["order_date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)
        .agg(
            orders=("Order ID", "nunique"),
            sales=("sales", "sum"),
            customers=("User ID", "nunique"),
        )
    )

    result = {
        "source": {
            "filename": source.name,
            "bytes": source.stat().st_size,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "rows": int(len(frame)),
            "columns": int(len(frame.columns)),
            "expected_columns": EXPECTED_COLUMNS,
            "schema_matches": len(frame.columns) == EXPECTED_COLUMNS,
            "duplicate_order_ids": int(frame["Order ID"].duplicated().sum()),
            "date_format": "MM/DD/YYYY",
            "date_min": parsed_dates.min().date().isoformat(),
            "date_max": parsed_dates.max().date().isoformat(),
            "invalid_dates": int(parsed_dates.isna().sum()),
        },
        "quality": {
            "valid_transactions": int(source_valid.sum()),
            "excluded_transactions": int((~source_valid).sum()),
            "valid_transaction_rate": float(source_valid.mean()),
            "analysis_transactions": int(analysis_eligible.sum()),
            "analysis_rate": float(analysis_eligible.sum() / source_valid.sum()) if source_valid.sum() else 0.0,
            "plausibility_excluded_transactions": int(plausibility_excluded.sum()),
            "high_value_excluded_transactions": int(high_value_excluded.sum()),
            "invalid_order_value_excluded_transactions": int(masks["invalid_order_value_excluded"].sum()),
            "source_valid_sales": float(sales[source_valid].sum()),
            "analysis_sales": float(sales[analysis_eligible].sum()),
            "plausibility_excluded_sales": float(sales[plausibility_excluded].sum()),
            "high_value_excluded_sales": float(sales[high_value_excluded].sum()),
            "zero_sales_rows": int(sales.eq(0).sum()),
            "missing_sales_rows": int(sales.isna().sum()),
            "unsupported_currency_rows": int((currency.ne("INR") & currency.notna()).sum()),
            "rating_coverage": float(frame["Restaurant Rating"].notna().mean()),
            "menu_coverage": float(frame["Menu_Item_Count"].notna().mean()),
            "restaurant_match_rate": float(
                frame["Restaurant Match"].astype("string").str.upper().eq("TRUE").mean()
            ),
        },
        "metrics": {
            "source_valid_gross_sales_inr": float(sales[source_valid].sum()),
            "analysis_gross_sales_inr": float(audited["sales"].sum()),
            "average_transaction_value_inr": float(audited["sales"].mean()),
            "median_transaction_value_inr": float(order_value[analysis_eligible].median()),
            "active_customers": active_customers,
            "repeat_customers": repeat_customers,
            "repeat_customer_rate": repeat_customers / active_customers,
            "orders_per_customer": len(audited) / active_customers,
        },
        "cleaning": {
            "field": "Order Value",
            "rule": PLAUSIBILITY_RULE,
            "method": PLAUSIBILITY_METHOD,
            "max_order_value_inr": int(MAX_ORDER_VALUE_INR),
            "source_valid_distribution": plausibility_profile(order_value[source_valid]),
            "source_valid_transactions": int(source_valid.sum()),
            "analysis_transactions": int(analysis_eligible.sum()),
            "analysis_retention_rate": float(analysis_eligible.sum() / source_valid.sum()) if source_valid.sum() else 0.0,
            "plausibility_excluded_transactions": int(plausibility_excluded.sum()),
            "high_value_excluded_transactions": int(high_value_excluded.sum()),
            "plausibility_excluded_sales": float(sales[plausibility_excluded].sum()),
            "high_value_excluded_sales": float(sales[high_value_excluded].sum()),
            "source_valid_sales": float(sales[source_valid].sum()),
            "analysis_sales": float(sales[analysis_eligible].sum()),
        },
        "monthly": monthly.to_dict(orient="records"),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
