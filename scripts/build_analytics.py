#!/usr/bin/env python3
"""Build deployment-safe aggregate analytics from the source marketplace CSV."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


SEGMENT_ACTIONS = {
    "Champions": "Protect the experience; test referral and early-access benefits.",
    "Loyal": "Deepen habit with relevant reorder and discovery journeys.",
    "Potential loyalists": "Nudge the third order with personalised cuisine discovery.",
    "New customers": "Improve first-to-second-order activation within 30 days.",
    "At risk": "Test a re-engagement journey before value declines further.",
    "Dormant": "Use low-cost win-back tests; suppress after repeated inactivity.",
    "Occasional": "Learn the job-to-be-done before increasing incentive spend.",
}


def scalar(value):
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    return value


def segment_customer(row: pd.Series, cutoff: pd.Timestamp) -> str:
    recency = int((cutoff - row["last_order"]).days)
    frequency = int(row["orders"])
    tenure = int((cutoff - row["first_order"]).days)
    if frequency >= 2 and recency > 270:
        return "At risk"
    if frequency == 1 and recency > 270:
        return "Dormant"
    if frequency >= 4 and recency <= 180:
        return "Champions"
    if frequency >= 3:
        return "Loyal"
    if frequency == 2 and recency <= 180:
        return "Potential loyalists"
    if frequency == 1 and tenure <= 90:
        return "New customers"
    return "Occasional"


def cohort_table(frame: pd.DataFrame, max_cohorts: int = 8, months: int = 6) -> list[dict]:
    if frame.empty:
        return []
    events = frame[["customer_id", "month_start"]].drop_duplicates()
    first = events.groupby("customer_id")["month_start"].min().rename("cohort")
    events = events.join(first, on="customer_id")
    events["age"] = (
        (events["month_start"].dt.year - events["cohort"].dt.year) * 12
        + events["month_start"].dt.month
        - events["cohort"].dt.month
    )
    sizes = first.value_counts().sort_index()
    eligible = sizes[sizes >= 25].index[:max_cohorts]
    output = []
    for cohort in eligible:
        size = int(sizes.loc[cohort])
        cohort_events = events[events["cohort"].eq(cohort)]
        retention = []
        for age in range(months + 1):
            active = int(cohort_events.loc[cohort_events["age"].eq(age), "customer_id"].nunique())
            retention.append(round(active / size * 100, 1))
        output.append({"cohort": cohort.strftime("%b %Y"), "size": size, "retention": retention})
    return output


def build_scope(scope_all: pd.DataFrame, selected: pd.DataFrame, label: str, period: str) -> dict:
    if selected.empty:
        return {"label": label, "period": period, "empty": True}
    cutoff = selected["order_date"].max()
    customer = selected.groupby("customer_id", as_index=False).agg(
        orders=("order_id", "nunique"),
        sales=("sales", "sum"),
        first_order=("order_date", "min"),
        last_order=("order_date", "max"),
    )
    first_scope_order = scope_all.groupby("customer_id")["order_date"].min()
    selected = selected.copy()
    selected["first_scope_order"] = selected["customer_id"].map(first_scope_order)
    selected["is_acquisition_month"] = selected["month_start"].eq(selected["first_scope_order"].dt.to_period("M").dt.to_timestamp())
    customer["recency_days"] = (cutoff - customer["last_order"]).dt.days
    customer["segment"] = customer.apply(segment_customer, axis=1, cutoff=cutoff)

    active = int(customer["customer_id"].nunique())
    repeat = int(customer["orders"].ge(2).sum())
    monthly_rows = []
    for month, group in selected.groupby("month_start"):
        new_ids = group.loc[group["is_acquisition_month"], "customer_id"].nunique()
        monthly_rows.append({
            "month": month.strftime("%Y-%m"),
            "orders": int(group["order_id"].nunique()),
            "sales": float(group["sales"].sum()),
            "customers": int(group["customer_id"].nunique()),
            "new_customers": int(new_ids),
            "returning_customers": int(group.loc[~group["is_acquisition_month"], "customer_id"].nunique()),
        })

    segment_rows = []
    for name in SEGMENT_ACTIONS:
        ids = customer.loc[customer["segment"].eq(name), "customer_id"]
        subset = customer[customer["customer_id"].isin(ids)]
        if subset.empty:
            continue
        segment_rows.append({
            "segment": name,
            "customers": int(len(subset)),
            "customer_share": float(len(subset) / active),
            "orders": int(subset["orders"].sum()),
            "orders_per_customer": float(subset["orders"].mean()),
            "sales": float(subset["sales"].sum()),
            "sales_per_customer": float(subset["sales"].mean()),
            "repeat_rate": float(subset["orders"].ge(2).mean()),
            "median_recency": float(subset["recency_days"].median()),
            "action": SEGMENT_ACTIONS[name],
        })
    segment_rows.sort(key=lambda row: row["customers"], reverse=True)

    bins = []
    for label_value, mask in [
        ("1", customer["orders"].eq(1)),
        ("2", customer["orders"].eq(2)),
        ("3", customer["orders"].eq(3)),
        ("4", customer["orders"].eq(4)),
        ("5+", customer["orders"].ge(5)),
    ]:
        bins.append({"frequency": label_value, "customers": int(mask.sum())})

    top_segment = segment_rows[0]["segment"] if segment_rows else "Unavailable"
    return {
        "label": label,
        "period": period,
        "empty": False,
        "range": [selected["order_date"].min().date().isoformat(), cutoff.date().isoformat()],
        "metrics": {
            "valid_transactions": int(selected["order_id"].nunique()),
            "gross_sales": float(selected["sales"].sum()),
            "active_customers": active,
            "new_customers": int(customer["customer_id"].isin(first_scope_order[first_scope_order.between(selected["order_date"].min(), cutoff)].index).sum()),
            "repeat_customers": repeat,
            "repeat_rate": repeat / active,
            "orders_per_customer": float(customer["orders"].mean()),
            "average_transaction_value": float(selected["sales"].sum() / selected["order_id"].nunique()),
        },
        "monthly": monthly_rows,
        "frequency": bins,
        "segments": segment_rows,
        "cohorts": cohort_table(selected),
        "insight": {
            "headline": f"{top_segment} is the largest observed lifecycle segment",
            "evidence": f"{repeat / active:.1%} of active customers placed at least two valid transactions in this filtered scope.",
            "action": "Use cohort retention—not repeat rate alone—to judge whether acquisition is compounding.",
            "confidence": "Medium",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = args.source.expanduser().resolve()

    raw = pd.read_csv(source, low_memory=False, encoding="utf-8-sig")
    order_date = pd.to_datetime(raw["Order Date"], format="%m/%d/%Y", errors="coerce")
    sales = pd.to_numeric(raw["Sales Amount"], errors="coerce")
    quantity = pd.to_numeric(raw["Sales Quantity"], errors="coerce")
    currency = raw["Order Currency"].astype("string").str.upper().str.strip()
    valid_flag = raw["Sales Amount Valid"].astype("string").str.upper().eq("TRUE")
    valid = raw["Order ID"].notna() & order_date.notna() & valid_flag & sales.gt(0) & currency.eq("INR")

    frame = pd.DataFrame({
        "order_id": raw.loc[valid, "Order ID"].astype(str),
        "order_date": order_date[valid],
        "customer_id": raw.loc[valid, "User ID"].astype(str),
        "sales": sales[valid],
        "quantity": quantity[valid],
        "market": raw.loc[valid, "Restaurant City"].fillna("Unknown").astype(str).str.strip(),
    })
    frame["month_start"] = frame["order_date"].dt.to_period("M").dt.to_timestamp()
    frame["year"] = frame["order_date"].dt.year

    market_counts = frame.groupby("market")["order_id"].nunique().sort_values(ascending=False)
    top_markets = market_counts.head(8).index.tolist()
    years = sorted(frame["year"].unique().tolist())
    scopes = {}
    for market in ["All markets", *top_markets]:
        scope_all = frame if market == "All markets" else frame[frame["market"].eq(market)]
        scopes[f"{market}|All years"] = build_scope(scope_all, scope_all, market, "All years")
        for year in years:
            scopes[f"{market}|{year}"] = build_scope(scope_all, scope_all[scope_all["year"].eq(year)], market, str(year))

    market_summary = []
    for market in top_markets:
        subset = frame[frame["market"].eq(market)]
        per_customer = subset.groupby("customer_id")["order_id"].nunique()
        market_summary.append({
            "market": market,
            "orders": int(subset["order_id"].nunique()),
            "sales": float(subset["sales"].sum()),
            "customers": int(per_customer.size),
            "repeat_rate": float(per_customer.ge(2).mean()),
        })

    quality = {
        "raw_rows": int(len(raw)),
        "valid_transactions": int(valid.sum()),
        "excluded_transactions": int((~valid).sum()),
        "valid_rate": float(valid.mean()),
        "zero_sales": int(sales.eq(0).sum()),
        "missing_sales": int(sales.isna().sum()),
        "unsupported_currency": int((currency.ne("INR") & currency.notna()).sum()),
        "rating_coverage": float(raw["Restaurant Rating"].notna().mean()),
        "menu_coverage": float(raw["Menu_Item_Count"].notna().mean()),
        "restaurant_match_rate": float(raw["Restaurant Match"].astype("string").str.upper().eq("TRUE").mean()),
        "duplicate_order_ids": int(raw["Order ID"].duplicated().sum()),
        "invalid_dates": int(order_date.isna().sum()),
    }
    output = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "source": {
            "filename": source.name,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "rows": int(len(raw)),
            "columns": int(len(raw.columns)),
            "date_format": "MM/DD/YYYY",
            "date_min": order_date.min().date().isoformat(),
            "date_max": order_date.max().date().isoformat(),
        },
        "quality": quality,
        "filters": {"markets": ["All markets", *top_markets], "periods": ["All years", *map(str, years)]},
        "market_summary": market_summary,
        "scopes": scopes,
        "definitions": {
            "valid_transactions": "Distinct orders with an ID, a parsed MM/DD/YYYY date, a true source-validity flag, positive sales, and INR currency.",
            "repeat_rate": "Customers with at least two valid transactions in the filtered scope divided by active customers in that scope.",
            "cohort_retention": "Customers active at cohort age m divided by customers first observed in that acquisition month within the filtered scope.",
            "average_transaction_value": "Gross valid INR sales divided by valid transactions; not labelled AOV because the source grain is unverified.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, default=scalar, allow_nan=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {args.output} ({args.output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
