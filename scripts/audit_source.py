#!/usr/bin/env python3
"""Profile the source CSV and emit the audited foundation metrics as JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


EXPECTED_COLUMNS = 36


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    frame = pd.read_csv(source, low_memory=False, encoding="utf-8-sig")
    parsed_dates = pd.to_datetime(
        frame["Order Date"], format="%m/%d/%Y", errors="coerce"
    )
    sales = pd.to_numeric(frame["Sales Amount"], errors="coerce")
    quantity = pd.to_numeric(frame["Sales Quantity"], errors="coerce")
    valid_flag = frame["Sales Amount Valid"].astype("string").str.upper().eq("TRUE")
    currency = frame["Order Currency"].astype("string").str.upper().str.strip()
    valid = (
        frame["Order ID"].notna()
        & parsed_dates.notna()
        & valid_flag
        & sales.notna()
        & sales.gt(0)
        & currency.eq("INR")
    )

    audited = frame.loc[valid, ["Order ID", "User ID"]].copy()
    audited["order_date"] = parsed_dates[valid]
    audited["sales"] = sales[valid]
    audited["quantity"] = quantity[valid]
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
            "valid_transactions": int(valid.sum()),
            "excluded_transactions": int((~valid).sum()),
            "valid_transaction_rate": float(valid.mean()),
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
            "gross_sales_inr": float(audited["sales"].sum()),
            "average_transaction_value_inr": float(audited["sales"].mean()),
            "active_customers": active_customers,
            "repeat_customers": repeat_customers,
            "repeat_customer_rate": repeat_customers / active_customers,
            "orders_per_customer": len(audited) / active_customers,
        },
        "monthly": monthly.to_dict(orient="records"),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
