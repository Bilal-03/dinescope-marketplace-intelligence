"""Pure analytics helpers shared by the public Streamlit interface and tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


DATA_PATH = Path(__file__).parent / "app" / "data" / "analytics.json"
DEFAULT_WEIGHTS = {"demand": 25, "growth": 25, "reach": 20, "gap": 15, "quality": 15}
CONFIDENCE_FACTORS = {"High": 1.0, "Medium": 0.85, "Low": 0.65}


def load_analytics(path: Path = DATA_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def scope_key(market: str, period: str) -> str:
    return f"{market}|{period}"


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
        records.append(
            {
                "Rank": row["rank"],
                "Market": row["market"],
                "Cuisine": row["cuisine"],
                "Lab score": round(row["lab_score"], 1),
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


def valid_data_contract(data: dict[str, Any]) -> bool:
    required = {"source", "quality", "filters", "market_views", "cuisine_views", "scopes", "definitions"}
    return required.issubset(data) and data["quality"]["valid_transactions"] <= data["quality"]["raw_rows"]
