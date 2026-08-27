#!/usr/bin/env python3
"""Build deployment-safe aggregate analytics from the source marketplace CSV."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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

CITY_ALIASES = {
    "noida-1": "Noida",
    "north-goa": "Goa",
    "central-goa": "Goa",
    "allahabad": "Prayagraj",
    "pondicherry": "Puducherry",
    "trichy": "Tiruchirappalli",
    "hubli": "Hubballi",
    "belgaum": "Belagavi",
    "yamuna-nagar": "Yamunanagar",
}

REVIEWED_MARKETS = {
    "Ahmedabad", "Bangalore", "Bhopal", "Bhubaneswar", "Bikaner", "Chandigarh",
    "Chennai", "Delhi", "Faridabad", "Goa", "Gurgaon", "Hyderabad", "Indore",
    "Kanpur", "Kolkata", "Lucknow", "Mumbai", "Noida", "Patna", "Pune",
    "Prayagraj", "Surat", "Udaipur", "Varanasi", "Vijayawada",
}

STATE_BY_MARKET = {
    "Ahmedabad": "Gujarat", "Bangalore": "Karnataka", "Bhopal": "Madhya Pradesh",
    "Bhubaneswar": "Odisha", "Bikaner": "Rajasthan", "Chandigarh": "Chandigarh",
    "Chennai": "Tamil Nadu", "Delhi": "Delhi", "Faridabad": "Haryana",
    "Goa": "Goa", "Gurgaon": "Haryana", "Hyderabad": "Telangana",
    "Indore": "Madhya Pradesh", "Kanpur": "Uttar Pradesh", "Kolkata": "West Bengal",
    "Lucknow": "Uttar Pradesh", "Mumbai": "Maharashtra", "Noida": "Uttar Pradesh",
    "Patna": "Bihar", "Pune": "Maharashtra", "Prayagraj": "Uttar Pradesh",
    "Surat": "Gujarat", "Udaipur": "Rajasthan", "Varanasi": "Uttar Pradesh",
    "Vijayawada": "Andhra Pradesh",
}


def canonical_city(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip(" ,-_")
    if not cleaned or cleaned.lower() in {"unknown", "nan", "none"}:
        return "Unknown"
    alias = CITY_ALIASES.get(cleaned.lower())
    if alias:
        return alias
    return cleaned.title().replace("Ncr", "NCR").replace("Pcmc", "PCMC")


def map_location(raw_city: str) -> dict:
    raw_city = re.sub(r"\s+", " ", str(raw_city)).strip()
    if not raw_city or raw_city.lower() in {"unknown", "nan", "none"}:
        return {"clean_city": "Unknown", "metro_region": "Unknown", "state": "Unknown", "confidence": "Low", "review_status": "Needs source enrichment"}
    suffix = raw_city.split(",")[-1]
    clean = canonical_city(suffix if "," in raw_city else raw_city)
    reviewed = clean in REVIEWED_MARKETS or clean in CITY_ALIASES.values()
    return {
        "clean_city": clean,
        "metro_region": clean,
        "state": STATE_BY_MARKET.get(clean, "Unmapped"),
        "confidence": "High" if reviewed else "Medium",
        "review_status": "Reviewed rule" if reviewed else "Review pending",
    }


def build_location_mapping(raw_market: pd.Series) -> pd.DataFrame:
    counts = raw_market.fillna("Unknown").astype(str).str.strip().value_counts(dropna=False)
    rows = []
    for raw_city, count in counts.items():
        rows.append({"raw_city": raw_city, **map_location(raw_city), "row_count": int(count)})
    return pd.DataFrame(rows).sort_values(["row_count", "raw_city"], ascending=[False, True])


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


def comparison_window(frame: pd.DataFrame, period: str) -> tuple[pd.DataFrame, pd.DataFrame, str, str]:
    if period == "All years":
        current_end = frame["order_date"].max()
        current_start = current_end - pd.Timedelta(days=364)
        previous_end = current_start - pd.Timedelta(days=1)
        previous_start = previous_end - pd.Timedelta(days=364)
    else:
        year = int(period)
        available = frame[frame["year"].eq(year)]
        if available.empty:
            return available, available, "No current window", "No comparison window"
        current_start = available["order_date"].min()
        current_end = available["order_date"].max()
        previous_start = current_start - pd.DateOffset(years=1)
        previous_end = current_end - pd.DateOffset(years=1)
    current = frame[frame["order_date"].between(current_start, current_end)]
    previous = frame[frame["order_date"].between(previous_start, previous_end)]
    current_label = f"{current_start:%d %b %Y}–{current_end:%d %b %Y}"
    previous_label = f"{previous_start:%d %b %Y}–{previous_end:%d %b %Y}"
    return current, previous, current_label, previous_label


def build_market_view(frame: pd.DataFrame, period: str) -> dict:
    current, previous, current_label, previous_label = comparison_window(frame, period)
    if current.empty:
        return {"period": period, "empty": True, "markets": []}
    current_total = int(current["order_id"].nunique())
    rows = []
    for market, group in current.groupby("clean_market"):
        if market == "Unknown":
            continue
        previous_group = previous[previous["clean_market"].eq(market)]
        per_customer = group.groupby("customer_id")["order_id"].nunique()
        orders = int(group["order_id"].nunique())
        previous_orders = int(previous_group["order_id"].nunique())
        sales_value = float(group["sales"].sum())
        previous_sales = float(previous_group["sales"].sum())
        high_mapping_share = float(group["mapping_confidence"].eq("High").mean())
        if orders >= 500 and high_mapping_share >= 0.8:
            confidence = "High"
        elif orders >= 200:
            confidence = "Medium"
        else:
            confidence = "Low"
        growth_orders = (orders - previous_orders) / previous_orders if previous_orders >= 50 else None
        growth_sales = (sales_value - previous_sales) / previous_sales if previous_sales > 0 else None
        monthly_orders = [
            {"month": month.strftime("%Y-%m"), "orders": int(month_group["order_id"].nunique())}
            for month, month_group in group.groupby("month_start")
        ]
        rows.append({
            "market": market,
            "orders": orders,
            "sales": sales_value,
            "customers": int(per_customer.size),
            "repeat_rate": float(per_customer.ge(2).mean()),
            "average_transaction_value": sales_value / orders,
            "order_share": orders / current_total,
            "previous_orders": previous_orders,
            "growth_orders": growth_orders,
            "growth_sales": growth_sales,
            "mapping_confidence": high_mapping_share,
            "confidence": confidence,
            "eligible_default": orders >= 200 and previous_orders >= 100 and growth_orders is not None,
            "monthly_orders": monthly_orders,
        })
    rows.sort(key=lambda row: row["orders"], reverse=True)
    eligible = [row for row in rows if row["eligible_default"]]
    top_five_share = sum(row["order_share"] for row in rows[:5])
    largest = rows[0] if rows else None
    fastest = max(eligible, key=lambda row: row["growth_orders"]) if eligible else None
    highest_repeat = max(eligible, key=lambda row: row["repeat_rate"]) if eligible else None
    return {
        "period": period,
        "empty": False,
        "current_window": current_label,
        "comparison_window": previous_label,
        "minimum_orders": 200,
        "markets": rows,
        "summary": {
            "active_markets": len(rows),
            "eligible_markets": len(eligible),
            "largest_market": largest["market"] if largest else None,
            "largest_market_orders": largest["orders"] if largest else 0,
            "fastest_growth_market": fastest["market"] if fastest else None,
            "fastest_growth_rate": fastest["growth_orders"] if fastest else None,
            "highest_repeat_market": highest_repeat["market"] if highest_repeat else None,
            "highest_repeat_rate": highest_repeat["repeat_rate"] if highest_repeat else None,
            "top_five_concentration": top_five_share,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mapping-output", type=Path, default=Path("data/mappings/location_mapping.csv"))
    args = parser.parse_args()
    source = args.source.expanduser().resolve()

    raw = pd.read_csv(source, low_memory=False, encoding="utf-8-sig")
    order_date = pd.to_datetime(raw["Order Date"], format="%m/%d/%Y", errors="coerce")
    sales = pd.to_numeric(raw["Sales Amount"], errors="coerce")
    quantity = pd.to_numeric(raw["Sales Quantity"], errors="coerce")
    currency = raw["Order Currency"].astype("string").str.upper().str.strip()
    valid_flag = raw["Sales Amount Valid"].astype("string").str.upper().eq("TRUE")
    valid = raw["Order ID"].notna() & order_date.notna() & valid_flag & sales.gt(0) & currency.eq("INR")

    raw_market = raw["Restaurant City"].fillna("Unknown").astype(str).str.strip()
    location_mapping = build_location_mapping(raw_market)
    mapping_by_raw = location_mapping.set_index("raw_city")
    frame = pd.DataFrame({
        "order_id": raw.loc[valid, "Order ID"].astype(str),
        "order_date": order_date[valid],
        "customer_id": raw.loc[valid, "User ID"].astype(str),
        "sales": sales[valid],
        "quantity": quantity[valid],
        "raw_market": raw_market[valid],
    })
    frame["clean_market"] = frame["raw_market"].map(mapping_by_raw["clean_city"])
    frame["mapping_confidence"] = frame["raw_market"].map(mapping_by_raw["confidence"])
    frame["month_start"] = frame["order_date"].dt.to_period("M").dt.to_timestamp()
    frame["year"] = frame["order_date"].dt.year

    market_counts = frame[frame["clean_market"].ne("Unknown")].groupby("clean_market")["order_id"].nunique().sort_values(ascending=False)
    top_markets = market_counts.head(12).index.tolist()
    years = sorted(frame["year"].unique().tolist())
    scopes = {}
    for market in ["All markets", *top_markets]:
        scope_all = frame if market == "All markets" else frame[frame["clean_market"].eq(market)]
        scopes[f"{market}|All years"] = build_scope(scope_all, scope_all, market, "All years")
        for year in years:
            scopes[f"{market}|{year}"] = build_scope(scope_all, scope_all[scope_all["year"].eq(year)], market, str(year))

    market_summary = []
    for market in top_markets:
        subset = frame[frame["clean_market"].eq(market)]
        per_customer = subset.groupby("customer_id")["order_id"].nunique()
        market_summary.append({
            "market": market,
            "orders": int(subset["order_id"].nunique()),
            "sales": float(subset["sales"].sum()),
            "customers": int(per_customer.size),
            "repeat_rate": float(per_customer.ge(2).mean()),
        })

    market_views = {period: build_market_view(frame, period) for period in ["All years", *map(str, years)]}

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
        "market_views": market_views,
        "location_mapping": {
            "raw_labels": int(len(location_mapping)),
            "mapped_rows": int(raw_market.ne("Unknown").sum()),
            "unknown_rows": int(raw_market.eq("Unknown").sum()),
            "high_confidence_rows": int(raw_market.map(mapping_by_raw["confidence"]).eq("High").sum()),
            "review_pending_labels": int(location_mapping["review_status"].eq("Review pending").sum()),
        },
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
    args.mapping_output.parent.mkdir(parents=True, exist_ok=True)
    location_mapping.to_csv(args.mapping_output, index=False)
    print(f"Wrote {args.output} ({args.output.stat().st_size:,} bytes)")
    print(f"Wrote {args.mapping_output} ({len(location_mapping):,} mapping rows)")


if __name__ == "__main__":
    main()
