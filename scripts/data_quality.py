"""Shared source-validity and order-value plausibility rules."""

from __future__ import annotations

from typing import Any

import pandas as pd


MAX_ORDER_VALUE_INR = 7_500.0
PLAUSIBILITY_RULE = "Order Value <= ₹7,500"
PLAUSIBILITY_METHOD = "Rounded 1.5×IQR upper fence from source-valid Order Value"


def build_quality_masks(frame: pd.DataFrame) -> dict[str, pd.Series]:
    """Return aligned source-validity and plausibility masks for a source frame."""

    order_date = pd.to_datetime(frame["Order Date"], format="%m/%d/%Y", errors="coerce")
    sales = pd.to_numeric(frame["Sales Amount"], errors="coerce")
    order_value = pd.to_numeric(frame["Order Value"], errors="coerce")
    quantity = pd.to_numeric(frame["Sales Quantity"], errors="coerce")
    currency = frame["Order Currency"].astype("string").str.upper().str.strip()
    valid_flag = frame["Sales Amount Valid"].astype("string").str.upper().eq("TRUE")

    source_valid = (
        frame["Order ID"].notna()
        & order_date.notna()
        & valid_flag
        & sales.notna()
        & sales.gt(0)
        & currency.eq("INR")
    )
    valid_order_value = order_value.notna() & order_value.gt(0)
    analysis_eligible = source_valid & valid_order_value & order_value.le(MAX_ORDER_VALUE_INR)
    high_value_excluded = source_valid & order_value.gt(MAX_ORDER_VALUE_INR)
    invalid_order_value_excluded = source_valid & ~valid_order_value

    return {
        "order_date": order_date,
        "sales": sales,
        "order_value": order_value,
        "quantity": quantity,
        "currency": currency,
        "valid_flag": valid_flag,
        "source_valid": source_valid,
        "analysis_eligible": analysis_eligible,
        "high_value_excluded": high_value_excluded,
        "invalid_order_value_excluded": invalid_order_value_excluded,
        "plausibility_excluded": source_valid & ~analysis_eligible,
    }


def plausibility_profile(order_values: pd.Series) -> dict[str, Any]:
    """Return the source-valid distribution statistics used to justify the cutoff."""

    values = pd.to_numeric(order_values, errors="coerce").dropna()
    q1 = float(values.quantile(0.25))
    q3 = float(values.quantile(0.75))
    iqr = q3 - q1
    return {
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "upper_fence": q3 + 1.5 * iqr,
    }
