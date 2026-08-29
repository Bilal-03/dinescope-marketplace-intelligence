#!/usr/bin/env python3
"""Build deployment-safe aggregate analytics from the source marketplace CSV."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from scripts.data_quality import (
        MAX_ORDER_VALUE_INR,
        PLAUSIBILITY_METHOD,
        PLAUSIBILITY_RULE,
        build_quality_masks,
        plausibility_profile,
    )
except ModuleNotFoundError:  # Direct ``python scripts/build_analytics.py`` execution.
    from data_quality import (
        MAX_ORDER_VALUE_INR,
        PLAUSIBILITY_METHOD,
        PLAUSIBILITY_RULE,
        build_quality_masks,
        plausibility_profile,
    )

AGGREGATE_VERSION = "1.3.0"
DISPLAY_YEAR_OFFSET = 6
EXPECTED_SOURCE_COLUMNS = 36
REQUIRED_SOURCE_COLUMNS = {
    "Order Date",
    "Sales Amount",
    "Sales Quantity",
    "Order Value",
    "Order Currency",
    "Sales Amount Valid",
    "Order ID",
    "User ID",
    "Restaurant City",
    "Restaurant Cuisine",
    "Restaurant Name",
    "Restaurant ID",
    "Restaurant Rating",
    "Menu_Item_Count",
    "Restaurant Match",
}


SEGMENT_ACTIONS = {
    "Champions": "Protect the experience; test referral and early-access benefits.",
    "Loyal": "Deepen habit with relevant reorder and discovery journeys.",
    "Potential loyalists": "Nudge the third order with personalised cuisine discovery.",
    "New customers": "Improve first-to-second-order activation within 30 days.",
    "At risk": "Test a re-engagement journey before value declines further.",
    "Dormant": "Use low-cost win-back tests; suppress after repeated inactivity.",
    "Occasional": "Learn the job-to-be-done before increasing incentive spend.",
}


def display_year_for_source(source_year: int) -> int:
    """Return the portfolio-facing year for a source calendar year."""

    return int(source_year) + DISPLAY_YEAR_OFFSET


def source_year_for_display(display_year: int) -> int:
    """Return the source calendar year represented by a display year."""

    return int(display_year) - DISPLAY_YEAR_OFFSET


def display_timestamp(value: pd.Timestamp) -> pd.Timestamp:
    """Shift a timestamp for presentation without changing analytical dates."""

    return value + pd.DateOffset(years=DISPLAY_YEAR_OFFSET)


def display_date_iso(value: pd.Timestamp) -> str:
    """Format a source timestamp as a portfolio-facing ISO date."""

    return display_timestamp(value).date().isoformat()


def display_month(value: pd.Timestamp) -> str:
    """Format a source month as a portfolio-facing YYYY-MM label."""

    return display_timestamp(value).strftime("%Y-%m")


def display_window_label(start: pd.Timestamp, end: pd.Timestamp) -> str:
    """Format a comparable window using portfolio-facing dates."""

    shifted_start = display_timestamp(start)
    shifted_end = display_timestamp(end)
    return f"{shifted_start:%d %b %Y}–{shifted_end:%d %b %Y}"


def validate_source_frame(frame: pd.DataFrame) -> None:
    """Fail before building when the source schema is not the audited contract."""

    missing = sorted(REQUIRED_SOURCE_COLUMNS.difference(frame.columns))
    if missing:
        raise ValueError(f"Source CSV is missing required columns: {', '.join(missing)}")
    if len(frame.columns) != EXPECTED_SOURCE_COLUMNS:
        raise ValueError(
            f"Source CSV has {len(frame.columns)} columns; expected {EXPECTED_SOURCE_COLUMNS}."
        )


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

CUISINE_ALIASES = {
    "pizzas": "Pizza", "pastas": "Pasta", "juices": "Juice", "thalis": "Thali",
    "kebabs": "Kebab", "italian-american": "Italian American", "pan-asian": "Pan Asian",
    "tex-mex": "Tex Mex", "beverage": "Beverages", "bakery products": "Bakery",
    "svanidhi street food vendor": "Street Food",
    "biryani - shivaji military hotel": "Biryani", "indian": "Indian",
}

INVALID_CUISINE_PATTERNS = (
    r"\buse code\b", r"\bcode valid\b", r"\bdiscount\b", r"\bfree delivery\b",
    r"\blimited stocks\b", r"\bcombos available\b", r"\bmax \d+ combos\b",
    r"^\d{1,2}:\d{2}\b", r"^default$", r"^popular brand store$",
)

CUISINE_GROUPS = {
    "Quick service & snacks": {"Fast Food", "Pizza", "Burgers", "Snacks", "Street Food", "Chaat", "Combo", "Kebab", "Grill", "Barbecue", "Pasta", "Tandoor"},
    "Desserts & beverages": {"Desserts", "Beverages", "Bakery", "Ice Cream", "Ice Cream Cakes", "Sweets", "Juice", "Waffle", "Paan", "Cafe"},
    "Health & home-style": {"Healthy Food", "Salads", "Keto", "Jain", "Home Food"},
    "Indian regional": {"Indian", "North Indian", "South Indian", "Biryani", "Mughlai", "Punjabi", "Bengali", "Maharashtrian", "Andhra", "Hyderabadi", "Kerala", "Gujarati", "Chettinad", "Rajasthani", "Bihari", "Goan", "Assamese", "Coastal", "Malwani", "Mangalorean", "North Eastern", "Lucknowi", "Awadhi", "Oriya", "Naga", "Kashmiri", "Sindhi", "Rayalaseema", "Telangana", "Konkan", "Parsi", "Khasi"},
}


def normalize_restaurant_name(value: str) -> str:
    if not value or str(value).lower() in {"nan", "none", "unknown"}:
        return "unknown"
    ascii_value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    ascii_value = ascii_value.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", ascii_value).strip() or "unknown"


def canonical_cuisine(value: str) -> tuple[str | None, str, str]:
    cleaned = re.sub(r"\s+", " ", str(value)).strip()
    if not cleaned:
        return None, "Invalid", "Excluded blank"
    lowered = cleaned.lower()
    if any(re.search(pattern, lowered) for pattern in INVALID_CUISINE_PATTERNS):
        return None, "Invalid", "Excluded non-cuisine label"
    canonical = CUISINE_ALIASES.get(lowered, cleaned.title())
    group = "Global & niche"
    for group_name, members in CUISINE_GROUPS.items():
        if canonical in members:
            group = group_name
            break
    return canonical, group, "Reviewed alias" if lowered in CUISINE_ALIASES else "Standardized label"


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


def build_cuisine_mapping(raw_cuisine: pd.Series) -> pd.DataFrame:
    tokens = raw_cuisine.fillna("").astype(str).str.split(",").explode().str.strip()
    counts = tokens[tokens.ne("")].value_counts()
    rows = []
    for raw_token, count in counts.items():
        canonical, group, status = canonical_cuisine(raw_token)
        rows.append({
            "raw_cuisine": raw_token,
            "canonical_cuisine": canonical or "Excluded",
            "cuisine_group": group,
            "confidence": "High" if canonical else "Low",
            "review_status": status,
            "row_count": int(count),
        })
    return pd.DataFrame(rows).sort_values(["row_count", "raw_cuisine"], ascending=[False, True])


def build_restaurant_mapping(raw_name: pd.Series, restaurant_id: pd.Series) -> pd.DataFrame:
    mapping = pd.DataFrame({
        "raw_name": raw_name.fillna("Unknown").astype(str),
        "restaurant_id": restaurant_id.fillna("Unknown").astype(str),
    })
    mapping["normalized_name"] = mapping["raw_name"].map(normalize_restaurant_name)
    grouped = mapping.groupby("normalized_name", as_index=False).agg(
        observed_rows=("raw_name", "size"),
        raw_name_variants=("raw_name", "nunique"),
        distinct_restaurant_ids=("restaurant_id", "nunique"),
    )
    grouped = grouped[grouped["observed_rows"].ge(2)].copy()
    grouped["confidence"] = np.where(grouped["raw_name_variants"].eq(1), "High", "Medium")
    grouped["review_status"] = np.where(grouped["observed_rows"].ge(20), "Priority review", "Conservative normalization")
    return grouped.sort_values(["observed_rows", "normalized_name"], ascending=[False, True])


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
        output.append({"cohort": display_timestamp(cohort).strftime("%b %Y"), "size": size, "retention": retention})
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
            "month": display_month(month),
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
        "range": [display_date_iso(selected["order_date"].min()), display_date_iso(cutoff)],
        "metrics": {
            "analysis_transactions": int(selected["order_id"].nunique()),
            "gross_sales": float(selected["sales"].sum()),
            "active_customers": active,
            "new_customers": int(customer["customer_id"].isin(first_scope_order[first_scope_order.between(selected["order_date"].min(), cutoff)].index).sum()),
            "repeat_customers": repeat,
            "repeat_rate": repeat / active,
            "orders_per_customer": float(customer["orders"].mean()),
            "average_transaction_value": float(selected["sales"].sum() / selected["order_id"].nunique()),
            "median_transaction_value": float(selected["order_value"].median()),
        },
        "monthly": monthly_rows,
        "frequency": bins,
        "segments": segment_rows,
        "cohorts": cohort_table(selected),
        "insight": {
            "headline": f"{top_segment} is the largest observed lifecycle segment",
            "evidence": f"{repeat / active:.1%} of active customers placed at least two included transactions in this filtered scope.",
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
        year = source_year_for_display(int(period))
        available = frame[frame["year"].eq(year)]
        if available.empty:
            return available, available, "No current window", "No comparison window"
        current_start = available["order_date"].min()
        current_end = available["order_date"].max()
        previous_start = current_start - pd.DateOffset(years=1)
        previous_end = current_end - pd.DateOffset(years=1)
    current = frame[frame["order_date"].between(current_start, current_end)]
    previous = frame[frame["order_date"].between(previous_start, previous_end)]
    current_label = display_window_label(current_start, current_end)
    previous_label = display_window_label(previous_start, previous_end)
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
            {"month": display_month(month), "orders": int(month_group["order_id"].nunique())}
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


def build_cuisine_bridge(frame: pd.DataFrame) -> pd.DataFrame:
    def tokens_for(value: str) -> list[str]:
        tokens = []
        for raw_token in str(value or "").split(","):
            canonical, _, _ = canonical_cuisine(raw_token)
            if canonical and canonical not in tokens:
                tokens.append(canonical)
        return tokens

    bridge = frame.copy()
    bridge["cuisine_tokens"] = bridge["cuisine_raw"].fillna("").map(tokens_for)
    bridge["cuisine_count"] = bridge["cuisine_tokens"].map(len)
    bridge = bridge[bridge["cuisine_count"].gt(0)].explode("cuisine_tokens").rename(columns={"cuisine_tokens": "cuisine"})
    bridge["allocation_weight"] = 1 / bridge["cuisine_count"]
    bridge["allocated_sales"] = bridge["sales"] * bridge["allocation_weight"]
    return bridge


def build_cuisine_view(bridge: pd.DataFrame, period: str) -> dict:
    current, previous, current_label, previous_label = comparison_window(bridge, period)
    if current.empty:
        return {"period": period, "empty": True, "pairs": [], "cuisines": []}
    current_market_orders = current.groupby("clean_market")["allocation_weight"].sum()
    current_market_listings = current[current["normalized_restaurant_name"].ne("unknown")].groupby("clean_market")["normalized_restaurant_name"].nunique()
    previous_pair_orders = previous.groupby(["clean_market", "cuisine"])["allocation_weight"].sum()
    rows = []
    for (market, cuisine), group in current.groupby(["clean_market", "cuisine"]):
        if market == "Unknown":
            continue
        allocated_orders = float(group["allocation_weight"].sum())
        if allocated_orders < 10:
            continue
        previous_orders = float(previous_pair_orders.get((market, cuisine), 0))
        listings = int(group.loc[group["normalized_restaurant_name"].ne("unknown"), "normalized_restaurant_name"].nunique())
        market_orders = float(current_market_orders.get(market, allocated_orders))
        market_listings = int(current_market_listings.get(market, max(listings, 1)))
        demand_share = allocated_orders / market_orders if market_orders else 0
        listing_share = listings / market_listings if market_listings else 0
        gap_index = demand_share / listing_share if listing_share else None
        growth = (allocated_orders - previous_orders) / previous_orders if previous_orders >= 25 else None
        rating_coverage = float(np.average(group["has_rating"], weights=group["allocation_weight"]))
        menu_coverage = float(np.average(group["has_menu"], weights=group["allocation_weight"]))
        if allocated_orders >= 200 and previous_orders >= 75:
            confidence = "High"
        elif allocated_orders >= 75 and previous_orders >= 25:
            confidence = "Medium"
        else:
            confidence = "Low"
        rows.append({
            "market": market,
            "cuisine": cuisine,
            "allocated_orders": allocated_orders,
            "allocated_sales": float(group["allocated_sales"].sum()),
            "customers": int(group["customer_id"].nunique()),
            "observed_listings": listings,
            "demand_share": demand_share,
            "listing_share": listing_share,
            "demand_to_listing_index": gap_index,
            "previous_allocated_orders": previous_orders,
            "growth": growth,
            "rating_coverage": rating_coverage,
            "menu_coverage": menu_coverage,
            "confidence": confidence,
            "eligible_default": allocated_orders >= 100 and previous_orders >= 50 and growth is not None,
        })

    pairs = pd.DataFrame(rows)
    if not pairs.empty:
        pairs["demand_score"] = pairs["allocated_orders"].rank(pct=True)
        pairs["growth_score"] = pd.to_numeric(pairs["growth"], errors="coerce").fillna(-1).clip(-1, 2).rank(pct=True)
        pairs["reach_score"] = pairs["customers"].rank(pct=True)
        pairs["gap_score"] = pairs["demand_to_listing_index"].fillna(0).clip(0, 3).rank(pct=True)
        pairs["quality_score"] = ((pairs["rating_coverage"] + pairs["menu_coverage"]) / 2).rank(pct=True)
        pairs["base_opportunity_score"] = 100 * (
            .25 * pairs["demand_score"] + .25 * pairs["growth_score"] + .20 * pairs["reach_score"]
            + .15 * pairs["gap_score"] + .15 * pairs["quality_score"]
        )
        confidence_factor = pairs["confidence"].map({"High": 1.0, "Medium": .85, "Low": .65})
        pairs["opportunity_score"] = pairs["base_opportunity_score"] * confidence_factor

        def action_for(row: pd.Series) -> str:
            if row["menu_coverage"] < .04 and row["rating_coverage"] < .25:
                return "Improve category instrumentation before scaling a supply recommendation."
            if row["growth"] is not None and row["growth"] >= .20 and (row["demand_to_listing_index"] or 0) >= 1.1:
                return "Test cuisine supply acquisition and discovery placement in this market."
            if row["growth"] is not None and row["growth"] < -.10 and row["allocated_orders"] >= 150:
                return "Diagnose demand decline and customer mix before adding supply."
            return "Validate demand quality and listing breadth before changing investment."

        pairs["recommended_action"] = pairs.apply(action_for, axis=1)
        pairs = pairs.sort_values("opportunity_score", ascending=False)
        # The UI's lowest selectable evidence threshold is 50 allocated
        # transactions. Do not ship lower-evidence rows or internal scoring
        # components to the browser; this keeps the deployment payload bounded.
        pairs = pairs[pairs["allocated_orders"].ge(50)].drop(columns=[
            "demand_score", "growth_score", "reach_score", "gap_score",
            "quality_score", "base_opportunity_score",
        ])
        numeric_columns = pairs.select_dtypes(include=[np.number]).columns
        pairs[numeric_columns] = pairs[numeric_columns].round(6)

    cuisines = []
    for cuisine, group in current.groupby("cuisine"):
        cuisines.append({
            "cuisine": cuisine,
            "allocated_orders": float(group["allocation_weight"].sum()),
            "allocated_sales": float(group["allocated_sales"].sum()),
            "customers": int(group["customer_id"].nunique()),
            "markets": int(group.loc[group["clean_market"].ne("Unknown"), "clean_market"].nunique()),
            "observed_listings": int(group.loc[group["normalized_restaurant_name"].ne("unknown"), "normalized_restaurant_name"].nunique()),
        })
    cuisines.sort(key=lambda row: row["allocated_orders"], reverse=True)
    pair_records = pairs.astype(object).where(pd.notna(pairs), None).to_dict(orient="records") if not pairs.empty else []
    eligible = [row for row in pair_records if row["eligible_default"]]
    return {
        "period": period,
        "empty": False,
        "current_window": current_label,
        "comparison_window": previous_label,
        "minimum_allocated_orders": 100,
        "allocated_order_total": float(current["allocation_weight"].sum()),
        "covered_order_count": int(current["order_id"].nunique()),
        "cuisines": cuisines,
        "pairs": pair_records,
        "summary": {
            "active_cuisines": len(cuisines),
            "eligible_pairs": len(eligible),
            "top_cuisine": cuisines[0]["cuisine"] if cuisines else None,
            "top_cuisine_orders": cuisines[0]["allocated_orders"] if cuisines else 0,
            "top_opportunity_market": eligible[0]["market"] if eligible else None,
            "top_opportunity_cuisine": eligible[0]["cuisine"] if eligible else None,
            "top_opportunity_score": eligible[0]["opportunity_score"] if eligible else None,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mapping-output", type=Path, default=Path("data/mappings/location_mapping.csv"))
    parser.add_argument("--cuisine-mapping-output", type=Path, default=Path("data/mappings/cuisine_mapping.csv"))
    parser.add_argument("--restaurant-mapping-output", type=Path, default=Path("data/mappings/restaurant_name_mapping.csv"))
    parser.add_argument(
        "--cleaned-output",
        type=Path,
        default=Path("data/cleaned/zomato_business_complete_cleaned.csv"),
    )
    parser.add_argument(
        "--exclusion-audit-output",
        type=Path,
        default=Path("data/cleaned/zomato_business_complete_exclusion_audit.csv"),
    )
    args = parser.parse_args()
    source = args.source.expanduser().resolve()

    raw = pd.read_csv(source, low_memory=False, encoding="utf-8-sig")
    validate_source_frame(raw)
    masks = build_quality_masks(raw)
    order_date = masks["order_date"]
    sales = masks["sales"]
    order_value = masks["order_value"]
    quantity = masks["quantity"]
    currency = masks["currency"]
    source_valid = masks["source_valid"]
    analysis_eligible = masks["analysis_eligible"]
    high_value_excluded = masks["high_value_excluded"]
    plausibility_excluded = masks["plausibility_excluded"]
    plausibility_stats = plausibility_profile(order_value[source_valid])

    raw_market = raw["Restaurant City"].fillna("Unknown").astype(str).str.strip()
    location_mapping = build_location_mapping(raw_market)
    cuisine_mapping = build_cuisine_mapping(raw["Restaurant Cuisine"])
    restaurant_mapping = build_restaurant_mapping(raw["Restaurant Name"], raw["Restaurant ID"])
    mapping_by_raw = location_mapping.set_index("raw_city")
    frame = pd.DataFrame({
        "order_id": raw.loc[analysis_eligible, "Order ID"].astype(str),
        "order_date": order_date[analysis_eligible],
        "customer_id": raw.loc[analysis_eligible, "User ID"].astype(str),
        "sales": sales[analysis_eligible],
        "order_value": order_value[analysis_eligible],
        "quantity": quantity[analysis_eligible],
        "raw_market": raw_market[analysis_eligible],
        "restaurant_id": raw.loc[analysis_eligible, "Restaurant ID"].fillna("Unknown").astype(str),
        "restaurant_name": raw.loc[analysis_eligible, "Restaurant Name"].fillna("Unknown").astype(str),
        "cuisine_raw": raw.loc[analysis_eligible, "Restaurant Cuisine"].fillna("").astype(str),
        "rating": pd.to_numeric(raw.loc[analysis_eligible, "Restaurant Rating"], errors="coerce"),
        "menu_item_count": pd.to_numeric(raw.loc[analysis_eligible, "Menu_Item_Count"], errors="coerce"),
    })
    frame["normalized_restaurant_name"] = frame["restaurant_name"].map(normalize_restaurant_name)
    frame["has_rating"] = frame["rating"].notna()
    frame["has_menu"] = frame["menu_item_count"].notna()
    frame["clean_market"] = frame["raw_market"].map(mapping_by_raw["clean_city"])
    frame["mapping_confidence"] = frame["raw_market"].map(mapping_by_raw["confidence"])
    frame["month_start"] = frame["order_date"].dt.to_period("M").dt.to_timestamp()
    frame["year"] = frame["order_date"].dt.year

    market_counts = frame[frame["clean_market"].ne("Unknown")].groupby("clean_market")["order_id"].nunique().sort_values(ascending=False)
    top_markets = market_counts.head(12).index.tolist()
    years = sorted(frame["year"].unique().tolist())
    display_years = [display_year_for_source(year) for year in years]
    periods = ["All years", *map(str, display_years)]
    scopes = {}
    for market in ["All markets", *top_markets]:
        scope_all = frame if market == "All markets" else frame[frame["clean_market"].eq(market)]
        scopes[f"{market}|All years"] = build_scope(scope_all, scope_all, market, "All years")
        for year, display_year in zip(years, display_years):
            period = str(display_year)
            scopes[f"{market}|{period}"] = build_scope(
                scope_all,
                scope_all[scope_all["year"].eq(year)],
                market,
                period,
            )

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

    market_views = {period: build_market_view(frame, period) for period in periods}
    cuisine_bridge = build_cuisine_bridge(frame)
    cuisine_views = {period: build_cuisine_view(cuisine_bridge, period) for period in periods}

    restaurant_observations = []
    for normalized_name, group in frame[frame["normalized_restaurant_name"].ne("unknown")].groupby("normalized_restaurant_name"):
        if len(group) < 2:
            continue
        restaurant_observations.append({
            "normalized_name": normalized_name,
            "observed_rows": int(len(group)),
            "distinct_restaurant_ids": int(group["restaurant_id"].nunique()),
            "markets": int(group.loc[group["clean_market"].ne("Unknown"), "clean_market"].nunique()),
            "rating_coverage": float(group["has_rating"].mean()),
            "menu_coverage": float(group["has_menu"].mean()),
        })
    restaurant_observations.sort(key=lambda row: row["observed_rows"], reverse=True)
    restaurant_id_counts = raw["Restaurant ID"].dropna().astype(str).value_counts()

    source_valid_sales = float(sales[source_valid].sum())
    analysis_sales = float(sales[analysis_eligible].sum())
    plausibility_excluded_sales = float(sales[plausibility_excluded].sum())
    high_value_sales = float(sales[high_value_excluded].sum())
    analysis_transactions = int(analysis_eligible.sum())
    source_valid_transactions = int(source_valid.sum())

    quality = {
        "raw_rows": int(len(raw)),
        "valid_transactions": source_valid_transactions,
        "excluded_transactions": int((~source_valid).sum()),
        "valid_rate": float(source_valid.mean()),
        "analysis_transactions": analysis_transactions,
        "analysis_rate": analysis_transactions / source_valid_transactions if source_valid_transactions else 0.0,
        "plausibility_excluded_transactions": int(plausibility_excluded.sum()),
        "high_value_excluded_transactions": int(high_value_excluded.sum()),
        "invalid_order_value_excluded_transactions": int(masks["invalid_order_value_excluded"].sum()),
        "source_valid_sales": source_valid_sales,
        "analysis_sales": analysis_sales,
        "plausibility_excluded_sales": plausibility_excluded_sales,
        "high_value_excluded_sales": high_value_sales,
        "zero_sales": int(sales.eq(0).sum()),
        "missing_sales": int(sales.isna().sum()),
        "unsupported_currency": int((currency.ne("INR") & currency.notna()).sum()),
        "rating_coverage": float(raw["Restaurant Rating"].notna().mean()),
        "menu_coverage": float(raw["Menu_Item_Count"].notna().mean()),
        "missing_rating_rows": int(raw["Restaurant Rating"].isna().sum()),
        "missing_menu_attribute_rows": int(raw["Menu_Item_Count"].isna().sum()),
        "restaurant_match_rate": float(raw["Restaurant Match"].astype("string").str.upper().eq("TRUE").mean()),
        "duplicate_order_ids": int(raw["Order ID"].duplicated().sum()),
        "invalid_dates": int(order_date.isna().sum()),
    }
    output = {
        "aggregate_version": AGGREGATE_VERSION,
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "source": {
            "filename": source.name,
            "bytes": source.stat().st_size,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "rows": int(len(raw)),
            "columns": int(len(raw.columns)),
            "expected_columns": EXPECTED_SOURCE_COLUMNS,
            "schema_matches": len(raw.columns) == EXPECTED_SOURCE_COLUMNS,
            "date_format": "MM/DD/YYYY",
            "date_min": display_date_iso(order_date.min()),
            "date_max": display_date_iso(order_date.max()),
        },
        "quality": quality,
        "cleaning": {
            "field": "Order Value",
            "rule": PLAUSIBILITY_RULE,
            "method": PLAUSIBILITY_METHOD,
            "max_order_value_inr": int(MAX_ORDER_VALUE_INR),
            "source_valid_distribution": plausibility_stats,
            "source_valid_transactions": source_valid_transactions,
            "analysis_transactions": analysis_transactions,
            "analysis_retention_rate": analysis_transactions / source_valid_transactions if source_valid_transactions else 0.0,
            "plausibility_excluded_transactions": int(plausibility_excluded.sum()),
            "high_value_excluded_transactions": int(high_value_excluded.sum()),
            "high_value_excluded_rate": float(high_value_excluded.sum() / source_valid_transactions) if source_valid_transactions else 0.0,
            "source_valid_sales": source_valid_sales,
            "analysis_sales": analysis_sales,
            "analysis_sales_retention_rate": analysis_sales / source_valid_sales if source_valid_sales else 0.0,
            "plausibility_excluded_sales": plausibility_excluded_sales,
            "high_value_excluded_sales": high_value_sales,
            "high_value_excluded_sales_share": high_value_sales / source_valid_sales if source_valid_sales else 0.0,
        },
        "filters": {"markets": ["All markets", *top_markets], "periods": periods},
        "market_summary": market_summary,
        "market_views": market_views,
        "cuisine_views": cuisine_views,
        "cuisine_mapping": {
            "raw_tokens": int(len(cuisine_mapping)),
            "canonical_cuisines": int(cuisine_mapping.loc[cuisine_mapping["canonical_cuisine"].ne("Excluded"), "canonical_cuisine"].nunique()),
            "excluded_token_rows": int(cuisine_mapping.loc[cuisine_mapping["canonical_cuisine"].eq("Excluded"), "row_count"].sum()),
            "cuisine_coverage": float(raw["Restaurant Cuisine"].notna().mean()),
        },
        "restaurant_mapping": {
            "raw_names": int(raw["Restaurant Name"].nunique()),
            "normalized_names": int(frame["normalized_restaurant_name"].nunique()),
            "repeat_normalized_names": int(len(restaurant_mapping)),
            "restaurant_ids": int(raw["Restaurant ID"].nunique()),
            "restaurant_ids_repeated": int(restaurant_id_counts.gt(1).sum()),
        },
        "restaurant_observations": restaurant_observations[:20],
        "location_mapping": {
            "raw_labels": int(len(location_mapping)),
            "mapped_rows": int(raw_market.ne("Unknown").sum()),
            "unknown_rows": int(raw_market.eq("Unknown").sum()),
            "high_confidence_rows": int(raw_market.map(mapping_by_raw["confidence"]).eq("High").sum()),
            "review_pending_labels": int(location_mapping["review_status"].eq("Review pending").sum()),
        },
        "scopes": scopes,
        "definitions": {
            "valid_transactions": "Source-valid distinct orders with an ID, a parsed MM/DD/YYYY date, a true source-validity flag, positive sales, and INR currency, before plausibility filtering.",
            "analysis_transactions": f"Source-valid distinct orders with a positive {PLAUSIBILITY_RULE}; this cleaned scope powers all project metrics.",
            "gross_sales": "Sum of positive INR Sales Amount for the plausibility-filtered analytical scope.",
            "repeat_rate": "Customers with at least two included analytical transactions in the filtered scope divided by active customers in that scope.",
            "cohort_retention": "Customers active at cohort age m divided by customers first observed in that acquisition month within the filtered scope.",
            "average_transaction_value": "Plausibility-filtered INR sales divided by included analytical transactions; not labelled AOV because the source grain is unverified.",
            "median_transaction_value": "Median Order Value among included analytical transactions in the filtered scope.",
            "rating_coverage": "Rows with a non-null Restaurant Rating divided by all source rows; this is an evidence-availability measure, not a quality score.",
            "menu_coverage": "Rows with a non-null Menu_Item_Count divided by all source rows; this is an evidence-availability measure, not a quality score.",
        },
    }
    if args.cleaned_output.expanduser().resolve() == source:
        raise ValueError("--cleaned-output must not overwrite the raw source CSV")
    if args.exclusion_audit_output.expanduser().resolve() == source:
        raise ValueError("--exclusion-audit-output must not overwrite the raw source CSV")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, default=scalar, allow_nan=False, separators=(",", ":")), encoding="utf-8")
    args.cleaned_output.parent.mkdir(parents=True, exist_ok=True)
    raw.loc[analysis_eligible].to_csv(args.cleaned_output, index=False)
    exclusion_columns = ["Order ID", "Order Date", "Order Value", "Sales Quantity", "Restaurant City"]
    exclusions = raw.loc[plausibility_excluded, exclusion_columns].copy()
    exclusions["Exclusion Reason"] = np.where(
        high_value_excluded.loc[plausibility_excluded],
        f"Order Value above ₹{MAX_ORDER_VALUE_INR:,.0f}",
        "Missing or non-positive Order Value",
    )
    args.exclusion_audit_output.parent.mkdir(parents=True, exist_ok=True)
    exclusions.to_csv(args.exclusion_audit_output, index=False)
    args.mapping_output.parent.mkdir(parents=True, exist_ok=True)
    location_mapping.to_csv(args.mapping_output, index=False)
    args.cuisine_mapping_output.parent.mkdir(parents=True, exist_ok=True)
    cuisine_mapping.to_csv(args.cuisine_mapping_output, index=False)
    args.restaurant_mapping_output.parent.mkdir(parents=True, exist_ok=True)
    restaurant_mapping.to_csv(args.restaurant_mapping_output, index=False)
    print(f"Wrote {args.output} ({args.output.stat().st_size:,} bytes)")
    print(f"Wrote {args.cleaned_output} ({len(raw.loc[analysis_eligible]):,} rows)")
    print(f"Wrote {args.exclusion_audit_output} ({len(exclusions):,} rows)")
    print(f"Wrote {args.mapping_output} ({len(location_mapping):,} mapping rows)")
    print(f"Wrote {args.cuisine_mapping_output} ({len(cuisine_mapping):,} mapping rows)")
    print(f"Wrote {args.restaurant_mapping_output} ({len(restaurant_mapping):,} repeat-name rows)")


if __name__ == "__main__":
    main()
