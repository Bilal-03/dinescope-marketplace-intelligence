"""DineScope public analytics workspace for Streamlit Community Cloud."""

from __future__ import annotations

from datetime import datetime
import hashlib
from pathlib import Path
import uuid

import altair as alt
import pandas as pd
import streamlit as st

from streamlit_lib import (
    DATA_PATH,
    DEFAULT_WEIGHTS,
    add_rank_movement,
    customer_cohort_frame,
    customer_mix_frame,
    cuisine_heatmap_frame,
    cuisine_ranking_frame,
    cuisine_summary_frame,
    decision_frame,
    decision_row_key,
    eligible_cuisine_pairs,
    eligible_market_rows,
    frequency_frame,
    lifecycle_frame,
    load_analytics,
    market_monthly_frame,
    market_ranking_frame,
    market_summary_frame,
    monthly_performance_frame,
    parse_feature_flags,
    rank_movement_label,
    reliability_issue_rows,
    restaurant_observation_frame,
    scenario_summary,
    score_decision_pairs,
    scope_key,
    valid_data_contract,
)


PAGE_OPTIONS = [
    "Overview",
    "Customer growth",
    "Market demand",
    "Cuisine gaps",
    "Data reliability",
    "Decision lab",
]

BRAND_NAME = "DineScope"
BRAND_DESCRIPTOR = "Food Marketplace Intelligence Platform"
BRAND_TAGLINE = "See demand. Understand customers. Prioritize growth."
BRAND_DESCRIPTION = (
    "An interactive decision-intelligence platform that helps Product and Growth teams "
    "uncover customer, market, restaurant, and cuisine opportunities from food-delivery data."
)
REPOSITORY_URL = "https://github.com/Bilal-03/dinescope-marketplace-intelligence"
BRAND_ASSETS = Path(__file__).parent / "assets" / "brand"
BRAND_LOCKUP = BRAND_ASSETS / "dinescope-lockup-light.png"
BRAND_ICON = BRAND_ASSETS / "favicon.png"
BRAND_ICON_LIGHT = BRAND_ASSETS / "dinescope-icon-light.png"
PAGE_FEATURE_FLAGS = {
    "Overview": "overview_v2",
    "Customer growth": "customers_v2",
    "Market demand": "markets_v2",
    "Cuisine gaps": "cuisines_v2",
    "Data reliability": "reliability_v2",
    "Decision lab": "decision_v2",
}
PAGE_COPY = {
    "Overview": {
        "eyebrow": "Product & Growth",
        "title": "Marketplace overview",
        "subtitle": "Understand customer momentum, value and where growth needs attention.",
    },
    "Customer growth": {
        "eyebrow": "First analytics module",
        "title": "Customer growth & retention",
        "subtitle": "Separate acquisition volume, repeat behavior and cohort retention.",
    },
    "Market demand": {
        "eyebrow": "Market intelligence",
        "title": "Market demand intelligence",
        "subtitle": "Compare meaningful scale, growth, value and market confidence.",
    },
    "Cuisine gaps": {
        "eyebrow": "Cuisine intelligence",
        "title": "Cuisine opportunity",
        "subtitle": "Find demand-to-coverage gaps without overstating restaurant performance.",
    },
    "Data reliability": {
        "eyebrow": "Foundation",
        "title": "Data reliability center",
        "subtitle": "See exactly what is trusted, excluded and limited before acting.",
    },
    "Decision lab": {
        "eyebrow": "Prioritisation sandbox",
        "title": "Decision lab",
        "subtitle": "Prioritise opportunities with adjustable evidence and confidence weights.",
    },
}


BASE_DECISION_SCENARIO = {
    "id": "balanced",
    "name": "Balanced guardrails",
    "weights": DEFAULT_WEIGHTS.copy(),
    "confidence_discount": True,
}
DECISION_WEIGHT_LABELS = {
    "demand": "Demand scale",
    "growth": "Growth momentum",
    "reach": "Customer reach",
    "gap": "Coverage gap",
    "quality": "Data quality",
}
DECISION_WEIGHT_HELP = {
    "demand": "Allocated transactions in the current window.",
    "growth": "Comparable-window transaction growth.",
    "reach": "Distinct customers reached by the pair.",
    "gap": "Relative demand-to-listing index.",
    "quality": "Rating and menu field coverage.",
}
LIFECYCLE_DEFINITIONS = {
    "New customers": "One observed order and a first order within the last 90 days of the selected scope.",
    "Potential loyalists": "Exactly two observed orders, with the latest order within the last 180 days.",
    "Loyal": "Three or more observed orders, with recency or frequency indicating an established habit.",
    "Champions": "Four or more observed orders and a latest order within the last 180 days.",
    "Occasional": "The remaining customers with some observed activity but no stronger lifecycle signal.",
    "At risk": "Two or more observed orders, but no order in the last 270 days of the selected scope.",
    "Dormant": "Exactly one observed order and no order in the last 270 days of the selected scope.",
}


st.set_page_config(
    page_title="DineScope · Food Marketplace Intelligence",
    page_icon=str(BRAND_ICON),
    layout="wide",
    initial_sidebar_state="expanded",
)
st.logo(
    str(BRAND_LOCKUP),
    size="large",
    link=REPOSITORY_URL,
    icon_image=str(BRAND_ICON_LIGHT),
)


@st.cache_data(show_spinner="Loading audited analytics…")
def analytics(artifact_sha256: str) -> dict:
    """Load analytics with cache invalidation tied to the published artifact.

    Streamlit can retain cached values while pulling a new repository revision.
    Including the artifact fingerprint prevents a previous contract version from
    being reused after ``data/analytics.json`` changes.
    """

    payload = load_analytics()
    if not valid_data_contract(payload):
        raise ValueError("The published analytics artifact does not satisfy the DineScope data contract.")
    return payload


def initialise_session_state(data: dict) -> None:
    """Seed stable widget state without overwriting an analyst's active choices."""

    defaults = {
        "pl_page": "Overview",
        "pl_market": "All markets",
        "pl_period": data["filters"]["periods"][0],
        "pl_methodology_open": False,
        "pl_market_minimum": 200,
        "pl_market_sort": "Rank by transactions",
        "pl_market_sort_previous": "Rank by transactions",
        "pl_selected_market": "",
        "pl_cuisine_minimum": 100,
        "pl_cuisine_sort": "Rank by opportunity signal",
        "pl_cuisine_sort_previous": "Rank by opportunity signal",
        "pl_cuisine_scope_previous": "",
        "pl_selected_cuisine": "",
        "pl_decision_minimum": 100,
        "pl_decision_confidence_discount": True,
        "pl_decision_scenario_name": "",
        "pl_decision_comparison_id": "balanced",
        "pl_decision_comparison_name": BASE_DECISION_SCENARIO["name"],
        "pl_decision_scenarios": [
            {
                **BASE_DECISION_SCENARIO,
                "weights": BASE_DECISION_SCENARIO["weights"].copy(),
            }
        ],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    for weight_key, default in DEFAULT_WEIGHTS.items():
        st.session_state.setdefault(f"pl_decision_weight_{weight_key}", default)
    if st.session_state["pl_market"] not in data["filters"]["markets"]:
        st.session_state["pl_market"] = "All markets"
    if st.session_state["pl_period"] not in data["filters"]["periods"]:
        st.session_state["pl_period"] = data["filters"]["periods"][0]
    if st.session_state["pl_page"] not in PAGE_OPTIONS:
        st.session_state["pl_page"] = "Overview"


def handle_page_change() -> None:
    """Market Demand compares all cleaned markets; detail selection must not leak into its cohort."""

    if st.session_state.get("pl_page") == "Market demand":
        st.session_state["pl_market"] = "All markets"


def reset_filter_state() -> None:
    st.session_state["pl_market"] = "All markets"
    st.session_state["pl_period"] = "All years"
    st.session_state["pl_market_minimum"] = 200
    st.session_state["pl_market_sort"] = "Rank by transactions"
    st.session_state["pl_market_sort_previous"] = "Rank by transactions"
    st.session_state["pl_selected_market"] = ""
    st.session_state["pl_cuisine_minimum"] = 100
    st.session_state["pl_cuisine_sort"] = "Rank by opportunity signal"
    st.session_state["pl_cuisine_sort_previous"] = "Rank by opportunity signal"
    st.session_state["pl_cuisine_scope_previous"] = ""
    st.session_state["pl_selected_cuisine"] = ""
    st.session_state["pl_decision_minimum"] = 100
    st.session_state["pl_decision_confidence_discount"] = True
    st.session_state["pl_decision_scenario_name"] = ""
    st.session_state["pl_decision_comparison_id"] = "balanced"
    st.session_state["pl_decision_comparison_name"] = BASE_DECISION_SCENARIO["name"]
    st.session_state["pl_decision_scenarios"] = [
        {**BASE_DECISION_SCENARIO, "weights": BASE_DECISION_SCENARIO["weights"].copy()}
    ]
    for weight_key, default in DEFAULT_WEIGHTS.items():
        st.session_state[f"pl_decision_weight_{weight_key}"] = default


def load_decision_scenario(scenario: dict) -> None:
    """Apply a session-only scenario before the next widget render."""

    for key, value in scenario.get("weights", {}).items():
        if key in DEFAULT_WEIGHTS:
            st.session_state[f"pl_decision_weight_{key}"] = int(value)
    st.session_state["pl_decision_confidence_discount"] = bool(scenario.get("confidence_discount", True))
    st.session_state["pl_decision_comparison_id"] = scenario.get("id", "balanced")
    st.session_state["pl_decision_comparison_name"] = scenario.get("name", BASE_DECISION_SCENARIO["name"])


def save_decision_scenario() -> None:
    """Save current scoring controls to Streamlit session state only."""

    name = str(st.session_state.get("pl_decision_scenario_name", "")).strip()
    if not name:
        return
    weights = {
        key: int(st.session_state.get(f"pl_decision_weight_{key}", default))
        for key, default in DEFAULT_WEIGHTS.items()
    }
    scenario = {
        "id": f"scenario-{uuid.uuid4().hex[:10]}",
        "name": name[:40],
        "weights": weights,
        "confidence_discount": bool(st.session_state.get("pl_decision_confidence_discount", True)),
    }
    scenarios = list(st.session_state.get("pl_decision_scenarios", []))
    scenarios.append(scenario)
    st.session_state["pl_decision_scenarios"] = scenarios
    st.session_state["pl_decision_scenario_name"] = ""
    st.session_state["pl_decision_comparison_id"] = scenario["id"]
    st.session_state["pl_decision_comparison_name"] = scenario["name"]


def remove_decision_scenario(scenario_id: str) -> None:
    """Delete a custom scenario from this session and fall back safely."""

    scenarios = [
        scenario
        for scenario in st.session_state.get("pl_decision_scenarios", [])
        if scenario.get("id") == BASE_DECISION_SCENARIO["id"] or scenario.get("id") != scenario_id
    ]
    st.session_state["pl_decision_scenarios"] = scenarios
    if st.session_state.get("pl_decision_comparison_id") == scenario_id:
        st.session_state["pl_decision_comparison_id"] = BASE_DECISION_SCENARIO["id"]
        st.session_state["pl_decision_comparison_name"] = BASE_DECISION_SCENARIO["name"]


def open_methodology() -> None:
    st.session_state["pl_methodology_open"] = True


def navigate_to_customer_growth() -> None:
    st.session_state["pl_page"] = "Customer growth"


def navigate_to_reliability() -> None:
    st.session_state["pl_page"] = "Data reliability"


def record_count(data: dict, page: str, market: str, period: str) -> tuple[int, str]:
    if page == "Market demand":
        view = data["market_views"].get(period, {})
        return len(view.get("markets", [])), "markets compared"
    if page in {"Cuisine gaps", "Decision lab"}:
        pairs = data["cuisine_views"].get(period, {}).get("pairs", [])
        count = len(pairs) if market == "All markets" else sum(row.get("market") == market for row in pairs)
        return count, "cuisine-market signals"
    scope = data["scopes"].get(scope_key(market, period), {})
    return int(scope.get("metrics", {}).get("analysis_transactions", 0)), "included records in view"


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root { --ink:#17211f; --muted:#65716d; --paper:#f7f5ef; --card:#fffdf8; --green:#194f46; --mint:#dcece5; --coral:#ef6a50; --amber:#e7a83e; }
        .stApp { background: radial-gradient(circle at 82% 3%, #f3decf 0, transparent 24rem), var(--paper); color:var(--ink); }
        [data-testid="stSidebar"] { background:#123c36; }
        [data-testid="stSidebar"] * { color:#f6f3e9 !important; }
        [data-testid="stSidebar"] [data-baseweb="select"] > div { background:#1c4c44; }
        [data-testid="stSidebar"] .stButton button,
        [data-testid="stSidebar"] .stButton button p,
        [data-testid="stSidebar"] .stButton button span { color:#123c36 !important; background:#fffdf8 !important; border-color:#fffdf8 !important; }
        [data-testid="stSidebar"] .stButton button:hover,
        [data-testid="stSidebar"] .stButton button:hover p,
        [data-testid="stSidebar"] .stButton button:hover span { color:#fffdf8 !important; background:#ef6a50 !important; border-color:#ef6a50 !important; }
        [data-testid="stSidebar"] .stButton button:focus-visible { outline:3px solid #ef6a50 !important; outline-offset:2px; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { overflow-wrap:anywhere; }
        .block-container { max-width:1480px; padding-top:2.4rem; padding-bottom:4rem; }
        .pl-hero { padding:1.5rem 0 1.2rem; border-bottom:1px solid #d9d6cd; margin-bottom:1.3rem; }
        .pl-kicker { color:var(--coral); font-size:.76rem; font-weight:800; letter-spacing:.15em; text-transform:uppercase; }
        .pl-hero h1 { font-family:Georgia,serif; font-size:clamp(2.2rem,5vw,4.4rem); line-height:.96; letter-spacing:-.045em; margin:.45rem 0 .75rem; color:var(--ink); }
        .pl-hero p { color:var(--muted); font-size:1.05rem; max-width:760px; margin:0; }
        .pl-chip { display:inline-block; background:var(--mint); color:var(--green); padding:.32rem .65rem; border-radius:99px; font-weight:700; font-size:.75rem; margin-top:.9rem; }
        .pl-filter-kicker { color:var(--muted); font-size:.72rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; margin:.2rem 0 .45rem; }
        .pl-section-kicker { display:block; color:var(--coral); font-size:.7rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; margin:.65rem 0 .15rem; }
        .pl-filter-meta { color:var(--muted); font-size:.78rem; line-height:1.45; padding:.45rem .55rem; border:1px solid #e2ded3; border-radius:10px; background:rgba(255,253,248,.72); }
        .pl-filter-meta b { color:var(--ink); font-size:.96rem; }
        div[data-testid="stMetric"] { background:rgba(255,253,248,.92); border:1px solid #e2ded3; border-radius:16px; padding:1rem 1.05rem; box-shadow:0 10px 26px rgba(36,50,46,.05); min-height:120px; }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] { color:var(--muted); font-weight:700; display:grid !important; grid-template-columns:minmax(0, 1fr) auto !important; column-gap:.25rem; align-items:start !important; white-space:normal !important; overflow:visible !important; text-overflow:clip !important; max-width:none !important; width:auto !important; overflow-wrap:anywhere; word-break:break-word; line-height:1.2; }
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] > div:first-child { display:flex !important; align-items:flex-start !important; flex-wrap:wrap !important; min-width:0 !important; max-width:100% !important; overflow:visible !important; }
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] [data-testid="stMarkdownContainer"] { display:block !important; white-space:normal !important; overflow:visible !important; text-overflow:clip !important; max-width:100% !important; min-width:0 !important; width:auto !important; overflow-wrap:anywhere; word-break:break-word; }
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] * { white-space:normal !important; overflow:visible !important; text-overflow:clip !important; overflow-wrap:anywhere; word-break:break-word; }
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] p { margin:0 !important; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"],
        div[data-testid="stMetric"] [data-testid="stMetricValue"] *,
        div[data-testid="stMetric"] [data-testid="stMetricValue"] p { color:var(--ink); font-family:Georgia,serif; white-space:normal !important; overflow:visible !important; text-overflow:clip !important; max-width:none !important; width:auto !important; overflow-wrap:anywhere; word-break:break-word; line-height:1.05; font-size:clamp(1.15rem, 1.9vw, 2.35rem); }
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] { display:inline-flex !important; flex-shrink:1 !important; white-space:normal !important; overflow:visible !important; text-overflow:clip !important; max-width:100% !important; min-width:0 !important; width:auto !important; overflow-wrap:anywhere; word-break:break-word; line-height:1.2; }
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] * { display:block !important; white-space:normal !important; overflow:visible !important; text-overflow:clip !important; max-width:100% !important; min-width:0 !important; width:auto !important; overflow-wrap:anywhere; word-break:break-word; line-height:1.2; }
        div[data-testid="stMetric"] { overflow:visible !important; }
        div[data-testid="stMetric"] [data-testid="stMarkdownContainer"],
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] > div,
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] > div { white-space:normal !important; overflow:visible !important; text-overflow:clip !important; max-width:100% !important; min-width:0 !important; overflow-wrap:anywhere; word-break:break-word; }
        div[data-testid="stMetric"] div:has(> [data-testid="stMetricDelta"]) { overflow:visible !important; flex-wrap:wrap !important; height:auto !important; }
        div[data-testid="stDataFrame"], div[data-testid="stTable"], .pl-note, .pl-callout { background:var(--card); border:1px solid #e2ded3; border-radius:14px; overflow:hidden; }
        .pl-note, .pl-callout { padding:1rem 1.15rem; color:var(--muted); }
        .pl-callout { border-left:5px solid var(--coral); }
        .pl-callout b { color:var(--ink); }
        h2, h3 { font-family:Georgia,serif !important; color:var(--ink) !important; letter-spacing:-.02em; }
        .stButton button, .stDownloadButton button { border-radius:99px; border:1px solid var(--green); color:var(--green); font-weight:750; white-space:normal; overflow-wrap:anywhere; line-height:1.2; min-height:2.5rem; }
        .stButton button:hover, .stDownloadButton button:hover { background:var(--green); color:white; }
        .stButton button:disabled { color:#8a948f !important; border-color:#cfd5d0 !important; background:rgba(255,253,248,.7) !important; opacity:1; }
        [data-testid="stDataFrame"] { max-width:100%; }
        /* Use the app-level Chart/Data table control so the native Vega
           "Show data" popover cannot strand a user without a return action. */
        [data-testid="stVegaLiteChart"] button[aria-label="Show data"],
        [data-testid="stVegaLiteChart"] button[title="Show data"],
        [data-testid="stElementToolbar"] button[aria-label="Show data"],
        [data-testid="stElementToolbar"] button[title="Show data"] { display:none !important; }
        [data-testid="stDialog"] [data-testid="stMarkdownContainer"] { overflow-wrap:anywhere; }
        div[data-testid="stHorizontalBlock"] { align-items:stretch; }
        @media (max-width: 900px) {
            /* Streamlit keeps its toolbar over the app on narrow screens.
               Keep the first hero line below that toolbar instead of letting
               the responsive padding pull it underneath the white header. */
            .block-container { padding:4rem 1rem 3rem; }
            div[data-testid="stHorizontalBlock"] { flex-wrap:wrap !important; }
            div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] { min-width:min(100%, 260px) !important; flex:1 1 260px !important; }
            .pl-hero h1 { font-size:clamp(2.15rem, 10vw, 3.6rem); }
            .pl-hero p { font-size:1rem; }
            h2, h3 { overflow-wrap:anywhere; }
            div[data-testid="stMetric"] { min-height:100px; padding:.8rem .85rem; }
            div[data-testid="stMetric"] [data-testid="stMetricValue"],
            div[data-testid="stMetric"] [data-testid="stMetricValue"] *,
            div[data-testid="stMetric"] [data-testid="stMetricValue"] p { font-size:clamp(1.1rem, 5.5vw, 1.9rem); }
            .stRadio > div { flex-wrap:wrap; row-gap:.35rem; }
        }
        [data-testid="stExpander"] { background:rgba(255,253,248,.72); border-radius:12px; }
        footer { visibility:hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def fmt_int(value: float | int) -> str:
    return f"{value:,.0f}"


def fmt_decimal(value: float | int) -> str:
    return f"{value:,.1f}"


def fmt_pct(value: float) -> str:
    return f"{value:.1%}"


def fmt_signed_pct(value: float | None) -> str:
    return "Not comparable" if value is None else f"{value:+.1%}"


def fmt_inr(value: float) -> str:
    if abs(value) >= 10_000_000:
        return f"₹{value / 10_000_000:.1f} Cr"
    if abs(value) >= 100_000:
        return f"₹{value / 100_000:.1f} L"
    return f"₹{value:,.0f}"


def render_chart_view(
    chart: alt.Chart | None,
    frame: pd.DataFrame,
    *,
    key: str,
    label: str,
    column_config: dict | None = None,
    renderer=None,
) -> None:
    """Render an explicit chart/data-table switch beside every analytical chart.

    Altair's native toolbar can open a data view, but it does not expose a
    reliable return control on every Streamlit viewport. Keeping the view in
    Streamlit state makes the switch back to the chart explicit and keyboard-
    accessible, while preserving the native download/fullscreen toolbar.
    """

    view = st.radio(label, ["Chart", "Data table"], horizontal=True, key=key)
    if view == "Data table":
        st.dataframe(
            frame,
            width="stretch",
            hide_index=True,
            column_config=column_config or {},
        )
    else:
        if renderer is not None:
            renderer()
        else:
            st.altair_chart(chart, width="stretch")


def render_lifecycle_explainer(scope: dict) -> None:
    """Explain the order-based lifecycle model before showing its table."""

    st.caption(
        "Yes — lifecycle segments describe food-delivery customer behaviour in the selected scope. "
        "They use included orders, order recency and observed spend; they are not app-activity or demographic labels."
    )
    with st.expander("How to read lifecycle segments and values"):
        st.markdown(
            "**Customers** is the number of unique customers in the segment. "
            "**Share** is that segment's share of active customers. "
            "**Orders / customer** and **Sales / customer** are averages of included transactions and filtered sales in the scope. "
            "**Repeat rate** is the share with at least two included orders. "
            "**Median recency** is the median days since a customer's last observed order."
        )
        definition_rows = [
            {"Segment": name, "Plain-language definition": definition}
            for name, definition in LIFECYCLE_DEFINITIONS.items()
            if any(row.get("segment") == name for row in scope.get("segments", []))
        ]
        if definition_rows:
            st.dataframe(
                pd.DataFrame(definition_rows),
                width="stretch",
                hide_index=True,
                column_config={
                    "Segment": st.column_config.TextColumn(width="medium"),
                    "Plain-language definition": st.column_config.TextColumn(width="large"),
                },
            )


def hero(page: str, subtitle: str, data: dict) -> None:
    generated = datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00")).strftime("%d %b %Y")
    copy = PAGE_COPY.get(page, {})
    eyebrow = copy.get("eyebrow", BRAND_NAME)
    title = copy.get("title", page)
    subtitle = copy.get("subtitle", subtitle)
    st.markdown(
        f'<section class="pl-hero"><span class="pl-kicker">{eyebrow} · {page}</span><h1>{title}</h1>'
        f'<p>{subtitle}</p><span class="pl-chip">Audited aggregate · refreshed {generated}</span></section>',
        unsafe_allow_html=True,
    )


def scope_payload(data: dict, market: str, period: str) -> dict:
    return data["scopes"][scope_key(market, period)]


@st.dialog("Metric dictionary & methodology", width="large")
def show_methodology(data: dict) -> None:
    st.write(
        "Definitions apply consistently across the global filters. The source CSV is transformed into deployment-safe aggregates; raw customer records and addresses are never sent to the browser."
    )
    source = data["source"]
    cleaning = data["cleaning"]
    st.subheader("Source contract")
    st.caption(
        f"Aggregate {data['aggregate_version']} · {source['filename']} · {source['rows']:,} rows · "
        f"{source['columns']} columns · {source['date_min']} — {source['date_max']}"
    )
    st.caption(f"SHA-256 · {source['sha256']}")
    st.subheader("Plausibility filter")
    st.info(
        f"Headline metrics use {cleaning['field']} at or below ₹{cleaning['max_order_value_inr']:,}. "
        f"The cutoff is the rounded IQR upper fence ({cleaning['source_valid_distribution']['upper_fence']:,.2f}); "
        f"{cleaning['high_value_excluded_transactions']:,} source-valid transactions remain in the audit but are excluded from project analytics."
    )
    st.subheader("Metric dictionary")
    definitions = data.get("definitions", {})
    for key, value in definitions.items():
        st.markdown(f"**{key.replace('_', ' ')}**  \n{value}")
    st.subheader("Public evidence boundary")
    st.info(
        "The public app exposes derived aggregates and reviewable mapping artifacts only. "
        "It does not forecast demand, prove unmet supply, or claim restaurant-level performance."
    )


def render_topbar(data: dict, flags: dict[str, bool]) -> None:
    left, right = st.columns([2.3, 1], gap="small")
    with left:
        st.markdown(f"### {BRAND_NAME}")
        st.caption(f"{BRAND_DESCRIPTOR} · {BRAND_TAGLINE}")
    with right:
        st.caption(f"Audited aggregate v{data['aggregate_version']}")
        st.caption("Public read-only · derived data only")


def render_global_filters(data: dict, page: str) -> tuple[str, str]:
    """Render the original global filter contract and return the effective scope."""

    st.markdown('<div class="pl-filter-kicker">Global filters</div>', unsafe_allow_html=True)
    columns = st.columns([1.05, 1.15, 1.1, 0.65, 1.4])
    with columns[0]:
        period = st.selectbox("Analysis period", data["filters"]["periods"], key="pl_period")
    if page == "Market demand":
        with columns[1]:
            st.caption("Comparison scope")
            st.button("All cleaned markets ✓", disabled=True, key="pl_comparison_scope")
        market = "All markets"
    else:
        with columns[1]:
            market = st.selectbox("Clean market", data["filters"]["markets"], key="pl_market")
    with columns[2]:
        st.caption("Transaction rule")
        st.button(
            f"INR + ₹{data['cleaning']['max_order_value_inr']:,} max ✓",
            disabled=True,
            key="pl_transaction_rule",
        )
    with columns[3]:
        st.caption("Actions")
        st.button("↻ Reset", key="pl_reset_filters", on_click=reset_filter_state)
    count, label = record_count(data, page, market, period)
    with columns[4]:
        st.caption("Source window")
        st.markdown(
            f'<div class="pl-filter-meta">{data["source"]["date_min"]} — {data["source"]["date_max"]}<br><b>{count:,}</b> {label}</div>',
            unsafe_allow_html=True,
        )
    return market, period


def render_sidebar(data: dict, flags: dict[str, bool]) -> str:
    with st.sidebar:
        if BRAND_LOCKUP.exists():
            st.image(str(BRAND_LOCKUP), width=230)
        else:
            st.markdown(f"## {BRAND_NAME}")
        st.caption(BRAND_TAGLINE)
        page = st.radio(
            "Workspace",
            PAGE_OPTIONS,
            key="pl_page",
            on_change=handle_page_change,
            label_visibility="collapsed",
        )
        st.divider()
        st.button("Metric dictionary", key="pl_methodology", on_click=open_methodology)
        st.caption(
            f"{data['quality']['valid_transactions']:,} source-valid · "
            f"{data['cleaning']['analysis_transactions']:,} included transactions"
        )
        st.caption("Public read-only analytics · no raw customer records")
        st.markdown(f"[Source, methods and support]({REPOSITORY_URL})")
        st.caption("Independent portfolio case study. Not affiliated with or endorsed by Zomato, Swiggy or another food-delivery company.")
        enabled = sum(flags.values())
        st.caption(f"Staged modules enabled · {enabled}/{len(flags)}")
    return page


def render_overview(data: dict, market: str, period: str) -> None:
    hero("Overview", "", data)
    scope = scope_payload(data, market, period)
    if scope["empty"]:
        st.warning("No included transactions are available for this market and period.")
        return
    metrics = scope["metrics"]
    cols = st.columns(5)
    cols[0].metric(
        "Included transactions",
        fmt_int(metrics["analysis_transactions"]),
        help=f"Distinct source-valid orders with Order Value at or below ₹{data['cleaning']['max_order_value_inr']:,}.",
    )
    cols[1].metric("Filtered sales", fmt_inr(metrics["gross_sales"]), help="Positive INR sales from included analytical transactions; source-valid sales remain in Data Reliability for audit.")
    cols[2].metric("Active customers", fmt_int(metrics["active_customers"]), help="Unique customers with at least one included transaction in scope.")
    cols[3].metric("Repeat customer rate", fmt_pct(metrics["repeat_rate"]), help="Customers with two or more included transactions divided by active customers; not cohort retention.")
    cols[4].metric("Avg. order value", fmt_inr(metrics["average_transaction_value"]), help="Filtered sales divided by included transactions. The median is shown in the cleaning note below.")
    st.caption(
        f"Plausibility-filtered scope · Order Value ≤ ₹{data['cleaning']['max_order_value_inr']:,} · "
        f"median order value {fmt_inr(metrics['median_transaction_value'])}"
    )
    left, right = st.columns([1.65, 1])
    with left:
        st.markdown('<span class="pl-section-kicker">Marketplace momentum</span>', unsafe_allow_html=True)
        st.subheader("Monthly performance")
        metric_label = st.radio(
            "Metric",
            ["Transactions", "Sales"],
            horizontal=True,
            key="pl_overview_metric",
        )
        metric = "orders" if metric_label == "Transactions" else "sales"
        monthly = monthly_performance_frame(scope, metric)
        value_title = "Included transactions" if metric == "orders" else "Filtered sales"
        value_format = ",.0f"
        chart = (
            alt.Chart(monthly)
            .mark_bar(color="#194f46" if metric == "orders" else "#ef6a50", cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X("Month:T", title=None, axis=alt.Axis(format="%b %y", tickCount=8, labelColor="#65716d")),
                y=alt.Y("Value:Q", title=value_title, axis=alt.Axis(format=value_format, labelColor="#65716d")),
                tooltip=[
                    alt.Tooltip("Month:T", title="Month", format="%b %Y"),
                    alt.Tooltip("Value:Q", title=value_title, format=value_format),
                ],
            )
            .properties(height=300)
            .configure_view(stroke=None)
            .configure_axis(gridColor="#e2ded3", titleColor="#65716d")
        )
        render_chart_view(
            chart,
            monthly,
            key="pl_overview_performance_view",
            label="Display monthly performance as",
            column_config={
                "Month": st.column_config.DatetimeColumn(format="MMM YYYY", width="medium"),
                "Value": st.column_config.NumberColumn(format="₹%,.0f" if metric == "sales" else "%,.0f", width="medium"),
                "Metric": st.column_config.TextColumn(width="medium"),
            },
        )
        st.caption(f"{value_title} · {len(monthly):,} monthly points · Partial boundary months remain labelled.")
    with right:
        st.markdown('<span class="pl-section-kicker">Decision brief</span>', unsafe_allow_html=True)
        st.subheader("What deserves attention")
        insight = scope["insight"]
        st.caption(f"{insight['confidence']} confidence")
        st.markdown(
            f'<div class="pl-callout"><b>{insight["headline"]}</b><p>{insight["evidence"]}</p></div>'
            f'<div class="pl-note"><b>Cleaning boundary</b><br>'
            f'Values above ₹{data["cleaning"]["max_order_value_inr"]:,} are excluded from headline analytics because they sit beyond the rounded IQR upper fence. The raw-valid impact remains visible in Data Reliability.</div>'
            f'<div class="pl-note"><b>Recommended next analysis</b><br>{insight["action"]}</div>',
            unsafe_allow_html=True,
        )
        st.button("Explore customer growth →", key="pl_explore_customers", on_click=navigate_to_customer_growth)
        st.caption("Descriptive evidence, not a causal claim or forecast.")
    lower_left, lower_right = st.columns([1.65, 1])
    with lower_left:
        st.markdown('<span class="pl-section-kicker">Demand footprint</span>', unsafe_allow_html=True)
        st.subheader("Highest-volume source markets")
        st.caption("Raw locality labels · mapping pending")
        market_table = market_summary_frame(data)
        st.dataframe(
            market_table,
            width="stretch",
            hide_index=True,
            column_config={
                "Market": st.column_config.TextColumn(width="medium"),
                "Filtered sales": st.column_config.NumberColumn(format="₹%.0f"),
                "Repeat rate": st.column_config.NumberColumn(format="percent"),
            },
        )
    with lower_right:
        st.markdown('<span class="pl-section-kicker">Evidence boundary</span>', unsafe_allow_html=True)
        st.subheader("Why recommendations stay cautious")
        st.write(
            f"Restaurant IDs almost never repeat, market labels mix locality and metro names, and menu coverage is only {fmt_pct(data['quality']['menu_coverage'])}. DineScope keeps those constraints visible instead of inventing precision."
        )
        st.button("Review source reliability →", key="pl_review_reliability", on_click=navigate_to_reliability)
    st.markdown('<span class="pl-section-kicker">Lifecycle signal</span>', unsafe_allow_html=True)
    st.subheader("Lifecycle mix")
    display = lifecycle_frame(scope)
    render_lifecycle_explainer(scope)
    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        column_config={
            "Segment": st.column_config.TextColumn(width="medium"),
            "Customers": st.column_config.NumberColumn(format="%,.0f", width="small"),
            "Share": st.column_config.NumberColumn(format="percent", width="small"),
            "Orders / customer": st.column_config.NumberColumn(format="%.2f", width="medium"),
            "Sales / customer": st.column_config.NumberColumn(format="₹%,.0f", width="medium"),
            "Repeat rate": st.column_config.NumberColumn(format="percent", width="small"),
            "Median recency": st.column_config.NumberColumn(format="%.0f days", width="medium"),
            "Suggested action": st.column_config.TextColumn(width="large", help="The recommended next growth experiment for this observed segment."),
        },
    )


def render_customers(data: dict, market: str, period: str) -> None:
    hero("Customer growth", "", data)
    st.caption(
        f"Customer metrics use the included analytical scope: Order Value ≤ ₹{data['cleaning']['max_order_value_inr']:,}."
    )
    scope = scope_payload(data, market, period)
    if scope["empty"]:
        st.warning("No included transactions are available for this market and period.")
        return
    metrics = scope["metrics"]
    cols = st.columns(5)
    cols[0].metric("Active customers", fmt_int(metrics["active_customers"]), help=f"Unique customers with an included transaction in {market} · {period}.")
    cols[1].metric("New customers", fmt_int(metrics["new_customers"]), help="Customers first observed in the selected scope.")
    cols[2].metric("Repeat customers", fmt_int(metrics["repeat_customers"]), help="Active customers with two or more included transactions in this scope.")
    cols[3].metric("Repeat customer rate", fmt_pct(metrics["repeat_rate"]), help="Repeat customers divided by active customers; distinct from cohort retention.")
    cols[4].metric("Transactions / customer", f'{metrics["orders_per_customer"]:.2f}', help="Included transactions divided by active customers.")
    left, right = st.columns([1.55, 1])
    with left:
        st.markdown('<span class="pl-section-kicker">Acquisition vs return</span>', unsafe_allow_html=True)
        st.subheader("Monthly active customer mix")
        st.caption("First observed in filtered market")
        monthly = customer_mix_frame(scope)
        chart = (
            alt.Chart(monthly)
            .mark_bar()
            .encode(
                x=alt.X("Month:T", title=None, axis=alt.Axis(format="%b %y", tickCount=8, labelColor="#65716d")),
                y=alt.Y("Customers:Q", title="Customers", stack="zero", axis=alt.Axis(format=",.0f", labelColor="#65716d")),
                color=alt.Color(
                    "Customer type:N",
                    title=None,
                    scale=alt.Scale(domain=["New customers", "Returning customers"], range=["#ef6a50", "#194f46"]),
                ),
                tooltip=[
                    alt.Tooltip("Month:T", title="Month", format="%b %Y"),
                    alt.Tooltip("Customer type:N", title="Type"),
                    alt.Tooltip("Customers:Q", title="Customers", format=",.0f"),
                ],
            )
            .properties(height=300)
            .configure_view(stroke=None)
            .configure_axis(gridColor="#e2ded3", titleColor="#65716d")
        )
        render_chart_view(
            chart,
            monthly,
            key="pl_customer_mix_view",
            label="Display customer mix as",
            column_config={
                "Month": st.column_config.DatetimeColumn(format="MMM YYYY", width="medium"),
                "Customer type": st.column_config.TextColumn(width="medium"),
                "Customers": st.column_config.NumberColumn(format="%,.0f", width="medium"),
            },
        )
        st.caption(f"{len(scope.get('monthly', [])):,} monthly points · New customers are first observed in the filtered market.")
    with right:
        st.markdown('<span class="pl-section-kicker">Habit depth</span>', unsafe_allow_html=True)
        st.subheader("Transaction frequency")
        frequency = frequency_frame(scope)
        chart = (
            alt.Chart(frequency)
            .mark_bar(color="#e7a83e", cornerRadiusEnd=4)
            .encode(
                y=alt.Y("Label:N", sort=None, title=None),
                x=alt.X("Customers:Q", title="Customers", axis=alt.Axis(format=",.0f", labelColor="#65716d")),
                tooltip=[
                    alt.Tooltip("Label:N", title="Frequency"),
                    alt.Tooltip("Customers:Q", title="Customers", format=",.0f"),
                ],
            )
            .properties(height=265)
            .configure_view(stroke=None)
            .configure_axis(gridColor="#e2ded3", titleColor="#65716d")
        )
        render_chart_view(
            chart,
            frequency,
            key="pl_customer_frequency_view",
            label="Display transaction frequency as",
            column_config={
                "Label": st.column_config.TextColumn(width="medium"),
                "Customers": st.column_config.NumberColumn(format="%,.0f", width="medium"),
            },
        )
        st.caption("Frequency is calculated inside the selected scope; it is not a lifetime app-engagement measure.")
    cohort_frame = customer_cohort_frame(scope.get("cohorts", []))
    cohort_left, cohort_right = st.columns([1.55, 1])
    with cohort_left:
        st.markdown('<span class="pl-section-kicker">True retention</span>', unsafe_allow_html=True)
        st.subheader("Acquisition cohort retention")
        st.caption("M0–M6 · Cohort size remains visible")
        if cohort_frame.empty:
            st.info("No cohort has enough evidence for a retention view in this scope.")
        else:
            percentage_columns = [column for column in cohort_frame.columns if column.startswith("M")]
            heatmap = cohort_frame.style.map(
                lambda value: f"background-color: rgba(25,79,70,{0.08 + min(float(value), 100) / 125:.2f}); color: {'white' if float(value) >= 55 else '#17211f'}"
                if pd.notna(value)
                else "",
                subset=percentage_columns,
            ).format({column: "{:.1f}%" for column in percentage_columns}, na_rep="—")
            st.dataframe(heatmap, width="stretch", hide_index=True)
        st.caption("M0 is acquisition month; later cells measure returned activity, not repeat rate.")
    with cohort_right:
        st.markdown('<span class="pl-section-kicker">Lifecycle signal</span>', unsafe_allow_html=True)
        st.subheader("Customer segment mix")
        segments = pd.DataFrame(scope.get("segments", []))
        if segments.empty:
            st.info("No lifecycle segments are available for this scope.")
        else:
            total = max(int(segments["customers"].sum()), 1)
            segment_chart = segments.head(6).assign(Share=lambda frame: frame["customers"] / total)
            chart = (
                alt.Chart(segment_chart)
                .mark_bar(color="#194f46", cornerRadiusEnd=4)
                .encode(
                    y=alt.Y("segment:N", sort="-x", title=None),
                    x=alt.X("Share:Q", title="Share", axis=alt.Axis(format=".0%", labelColor="#65716d")),
                    tooltip=[
                        alt.Tooltip("segment:N", title="Segment"),
                        alt.Tooltip("customers:Q", title="Customers", format=",.0f"),
                        alt.Tooltip("Share:Q", title="Share", format=".1%"),
                    ],
                )
                .properties(height=265)
                .configure_view(stroke=None)
                .configure_axis(gridColor="#e2ded3", titleColor="#65716d")
            )
            render_chart_view(
                chart,
                segment_chart,
                key="pl_customer_segment_mix_view",
                label="Display segment mix as",
                column_config={
                    "segment": st.column_config.TextColumn(label="Segment", width="medium"),
                    "customers": st.column_config.NumberColumn(label="Customers", format="%,.0f", width="medium"),
                    "Share": st.column_config.NumberColumn(format="percent", width="small"),
                },
            )
            insight = scope["insight"]
            st.markdown(
                f'<div class="pl-note"><b>{insight["headline"]}</b><br>{insight["action"]}<br><small>{insight["confidence"]} confidence</small></div>',
                unsafe_allow_html=True,
            )
    st.markdown('<span class="pl-section-kicker">Action workspace</span>', unsafe_allow_html=True)
    st.subheader("Segment evidence & recommended action")
    segment_table = lifecycle_frame(scope)
    render_lifecycle_explainer(scope)
    st.dataframe(
        segment_table,
        width="stretch",
        hide_index=True,
        column_config={
            "Segment": st.column_config.TextColumn(width="medium"),
            "Customers": st.column_config.NumberColumn(format="%,.0f", width="small"),
            "Share": st.column_config.NumberColumn(format="percent", width="small"),
            "Orders / customer": st.column_config.NumberColumn(format="%.2f", width="medium"),
            "Sales / customer": st.column_config.NumberColumn(format="₹%,.0f", width="medium"),
            "Repeat rate": st.column_config.NumberColumn(format="percent", width="small"),
            "Median recency": st.column_config.NumberColumn(format="%.0f days", width="medium"),
            "Suggested action": st.column_config.TextColumn(width="large", help="The recommended next growth experiment for this observed segment."),
        },
    )
    st.download_button(
        "Export customer segment evidence",
        segment_table.to_csv(index=False).encode("utf-8"),
        f"dinescope-segments-{market}-{period}.csv".replace(" ", "-").lower(),
        "text/csv",
        key="pl_customer_segment_export",
    )
    st.markdown('<div class="pl-note"><b>Interpretation boundary</b><br>Repeat customer rate is the share of active customers with at least two included transactions in the selected scope. Cohort retention is the stronger view for judging whether acquisition compounds.</div>', unsafe_allow_html=True)


def render_markets(data: dict, market: str, period: str) -> None:
    hero("Market demand", "", data)
    st.caption(
        f"Market metrics use the included analytical scope: Order Value ≤ ₹{data['cleaning']['max_order_value_inr']:,}."
    )
    view = data["market_views"][period]
    # Market Demand is intentionally a comparison surface across all cleaned
    # markets. The global market selector is disabled for this page so a detail
    # selection cannot silently turn the ranking into a single-market cohort.
    rows = view["markets"]
    if view["empty"] or not rows:
        st.warning("No comparable market evidence is available for this selection.")
        return

    summary = view["summary"]
    mapping = data["location_mapping"]

    # Keep the threshold and ranking controls in session state so changing a
    # control is reproducible in screenshots and does not reset the selected
    # market on every Streamlit rerun.
    minimum = st.slider(
        "Minimum current transactions",
        min_value=100,
        max_value=1000,
        step=100,
        key="pl_market_minimum",
        help="A market must also have at least half this volume (with a 50-transaction floor) in the previous comparable window.",
    )
    comparison_minimum = max(50, minimum / 2)
    eligible = eligible_market_rows(rows, minimum, 50)

    sort_options = {
        "Rank by transactions": "orders",
        "Rank by growth": "growth_orders",
        "Rank by repeat rate": "repeat_rate",
        "Rank by sales": "sales",
    }
    sort_label = st.selectbox("Rank markets by", list(sort_options), key="pl_market_sort")
    sort_field = sort_options[sort_label]
    if st.session_state.get("pl_market_sort_previous") != sort_label:
        # Re-seed the selected market from the newly ranked list. Preserve an
        # explicit diagnosis only while the ranking dimension stays unchanged.
        st.session_state["pl_market_sort_previous"] = sort_label
        st.session_state["pl_selected_market"] = ""
    ranked = sorted(
        eligible,
        key=lambda row: (
            -(row.get(sort_field) if row.get(sort_field) is not None else float("-inf")),
            str(row.get("market", "")),
        ),
    )
    names = [row["market"] for row in ranked]
    if not names:
        st.info("No market clears the current transaction and comparison evidence thresholds.")
        st.caption(
            f'{view["current_window"]} versus {view["comparison_window"]} · '
            f"growth requires at least {comparison_minimum:,.0f} previous-window transactions."
        )
        return
    if st.session_state.get("pl_selected_market") not in names:
        st.session_state["pl_selected_market"] = names[0]
    selected_name = st.selectbox("Selected market", names, key="pl_selected_market")
    selected = next(row for row in ranked if row["market"] == selected_name)

    fastest = max(
        eligible,
        key=lambda row: row.get("growth_orders") if row.get("growth_orders") is not None else float("-inf"),
        default=None,
    )
    highest_repeat = max(
        eligible,
        key=lambda row: row.get("repeat_rate") if row.get("repeat_rate") is not None else float("-inf"),
        default=None,
    )

    st.markdown(
        f'<div class="pl-filter-meta"><b>Current comparable window</b> {view["current_window"]} '
        f'&nbsp;·&nbsp; <b>Previous equal-length window</b> {view["comparison_window"]} '
        f'&nbsp;·&nbsp; <b>{len(eligible):,} eligible markets</b> at {minimum:,}+ current transactions</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        f"Growth also requires at least {comparison_minimum:,.0f} transactions in the comparison window. "
        "This prevents tiny bases from dominating the ranking."
    )

    cols = st.columns(5)
    cols[0].metric(
        "Active cleaned markets",
        fmt_int(summary["active_markets"]),
        f'{mapping["raw_labels"]:,} raw labels normalized',
    )
    cols[1].metric(
        "Largest market",
        summary["largest_market"] or "—",
        f'{summary["largest_market_orders"]:,} transactions',
    )
    cols[2].metric(
        "Fastest eligible growth",
        fastest["market"] if fastest else "—",
        fmt_signed_pct(fastest.get("growth_orders")) + " transactions" if fastest else "Insufficient comparison",
    )
    cols[3].metric(
        "Highest repeat rate",
        highest_repeat["market"] if highest_repeat else "—",
        fmt_pct(highest_repeat["repeat_rate"]) if highest_repeat else "Insufficient comparison",
    )
    cols[4].metric(
        "Top-five concentration",
        fmt_pct(summary["top_five_concentration"]),
        "Share of current transactions",
    )

    st.markdown('<span class="pl-section-kicker">Scale × momentum</span>', unsafe_allow_html=True)
    st.subheader("Market growth quadrant")
    st.caption("Select a market in the control above to diagnose it. The plot shows the top 30 eligible markets by current scale.")
    quadrant_rows = sorted(eligible, key=lambda row: row.get("orders", 0), reverse=True)[:30]
    quadrant = pd.DataFrame(
        [
            {
                "Market": row["market"],
                "Transactions": row["orders"],
                "Growth": row["growth_orders"],
                "Customers": row["customers"],
                "Repeat rate": row["repeat_rate"],
                "Avg. order value": row["average_transaction_value"],
                "Confidence": row["confidence"],
            }
            for row in quadrant_rows
        ]
    )
    if not quadrant.empty:
        point_chart = (
            alt.Chart(quadrant)
            .mark_circle(opacity=0.88, stroke="#fffdf8", strokeWidth=1.5)
            .encode(
                x=alt.X(
                    "Transactions:Q",
                    title="Current transactions (log scale)",
                    scale=alt.Scale(type="log"),
                    axis=alt.Axis(format=",.0f"),
                ),
                y=alt.Y("Growth:Q", title="Comparable transaction growth", axis=alt.Axis(format=".0%")),
                size=alt.Size("Transactions:Q", title="Scale", scale=alt.Scale(range=[70, 900]), legend=None),
                color=alt.Color(
                    "Confidence:N",
                    title="Confidence",
                    scale=alt.Scale(domain=["High", "Medium", "Low"], range=["#194f46", "#e7a83e", "#ef6a50"]),
                ),
                tooltip=[
                    alt.Tooltip("Market:N", title="Market"),
                    alt.Tooltip("Transactions:Q", title="Transactions", format=",.0f"),
                    alt.Tooltip("Growth:Q", title="Growth", format="+.1%"),
                    alt.Tooltip("Customers:Q", title="Customers", format=",.0f"),
                    alt.Tooltip("Repeat rate:Q", title="Repeat rate", format=".1%"),
                    alt.Tooltip("Confidence:N", title="Confidence"),
                ],
            )
            .properties(height=350)
        )
        zero_rule = alt.Chart(pd.DataFrame({"Growth": [0]})).mark_rule(color="#c8c2b5").encode(y="Growth:Q")
        median_transactions = float(quadrant["Transactions"].median())
        scale_rule = alt.Chart(pd.DataFrame({"Transactions": [median_transactions]})).mark_rule(color="#c8c2b5").encode(x="Transactions:Q")
        quadrant_chart = (
            (point_chart + zero_rule + scale_rule)
            .configure_view(stroke=None)
            .configure_axis(gridColor="#e2ded3", titleColor="#65716d", labelColor="#65716d")
        )
        render_chart_view(
            quadrant_chart,
            quadrant,
            key="pl_market_quadrant_view",
            label="Display market growth quadrant as",
            column_config={
                "Market": st.column_config.TextColumn(width="medium"),
                "Transactions": st.column_config.NumberColumn(format="%,.0f", width="medium"),
                "Growth": st.column_config.NumberColumn(format="+.1f%", width="medium"),
                "Customers": st.column_config.NumberColumn(format="%,.0f", width="medium"),
                "Repeat rate": st.column_config.NumberColumn(format="percent", width="medium"),
                "Avg. order value": st.column_config.NumberColumn(format="₹%,.0f", width="medium"),
                "Confidence": st.column_config.TextColumn(width="medium"),
            },
        )
        st.caption("Scale & protect · Investigate decline · Selective bets · Build evidence · Confidence is shown by colour.")

    st.markdown('<span class="pl-section-kicker">Selected market</span>', unsafe_allow_html=True)
    st.subheader(selected["market"])
    growth = selected.get("growth_orders")
    if growth is None:
        signal = "Comparison base is insufficient"
        action = "Protect the current base and collect a comparable history before changing investment."
    elif growth >= 0.2:
        signal = "Demand is expanding materially"
        action = (
            "Validate whether acquisition quality can improve: growth is strong, but within-window repeat behavior remains low."
            if selected.get("repeat_rate", 0) < 0.02
            else "Protect the current base and compare customer mix before changing investment."
        )
    elif growth < -0.1:
        signal = "Demand is contracting"
        action = "Diagnose category, customer-mix and instrumentation shifts before committing incremental growth spend."
    else:
        signal = "Demand is broadly stable"
        action = "Protect the current base and compare customer mix before changing investment."
    st.markdown(
        f'<div class="pl-callout"><b>{signal}</b><br>{action}<br><small>{selected["confidence"]} confidence · Recommended actions are diagnostic hypotheses, not causal conclusions.</small></div>',
        unsafe_allow_html=True,
    )
    detail_cols = st.columns(5)
    detail_cols[0].metric("Transaction growth", fmt_signed_pct(growth), f'{selected["previous_orders"]:,} → {selected["orders"]:,} transactions')
    detail_cols[1].metric("Customer reach", fmt_int(selected["customers"]))
    detail_cols[2].metric("Repeat rate", fmt_pct(selected["repeat_rate"]))
    detail_cols[3].metric("Average order value", fmt_inr(selected["average_transaction_value"]))
    detail_cols[4].metric("Transaction share", fmt_pct(selected["order_share"]))

    st.markdown('<span class="pl-section-kicker">Comparable movement</span>', unsafe_allow_html=True)
    st.subheader("Monthly transaction pulse")
    st.caption("Top eligible markets by current scale")
    pulse = market_monthly_frame(ranked[:4])
    if not pulse.empty:
        pulse_chart = (
            alt.Chart(pulse)
            .mark_bar(color="#194f46", cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X("Month:T", title=None, axis=alt.Axis(format="%b %y", labelColor="#65716d", tickCount=8)),
                y=alt.Y("Transactions:Q", title="Transactions", axis=alt.Axis(format=",.0f", labelColor="#65716d")),
                column=alt.Column("Market:N", title=None, sort=[row["market"] for row in ranked[:4]]),
                tooltip=[
                    alt.Tooltip("Market:N", title="Market"),
                    alt.Tooltip("Month:T", title="Month", format="%b %Y"),
                    alt.Tooltip("Transactions:Q", title="Transactions", format=",.0f"),
                ],
            )
            .properties(height=150)
            .configure_view(stroke=None)
            .configure_axis(gridColor="#e2ded3", titleColor="#65716d")
        )
        render_chart_view(
            pulse_chart,
            pulse,
            key="pl_market_pulse_view",
            label="Display monthly transaction pulse as",
            column_config={
                "Market": st.column_config.TextColumn(width="medium"),
                "Month": st.column_config.DatetimeColumn(format="MMM YYYY", width="medium"),
                "Transactions": st.column_config.NumberColumn(format="%,.0f", width="medium"),
            },
        )

    st.markdown('<span class="pl-section-kicker">Evidence table</span>', unsafe_allow_html=True)
    st.subheader("Eligible market ranking")
    table = market_ranking_frame(ranked)
    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        column_config={
            "Transactions": st.column_config.NumberColumn(format="%,.0f"),
            "Growth": st.column_config.NumberColumn(format="+.1f%"),
            "Customers": st.column_config.NumberColumn(format="%,.0f"),
            "Repeat rate": st.column_config.NumberColumn(format="percent"),
            "Avg. order value": st.column_config.NumberColumn(format="₹%,.0f"),
            "Txn share": st.column_config.NumberColumn(format="percent"),
        },
    )
    st.download_button(
        "Export market ranking",
        table.to_csv(index=False).encode("utf-8"),
        f"dinescope-market-ranking-{period}.csv",
        "text/csv",
        key="pl_market_ranking_export",
    )
    mapped_share = mapping["mapped_rows"] / max(mapping["mapped_rows"] + mapping["unknown_rows"], 1)
    st.markdown(
        f'<div class="pl-note"><b>Mapping coverage</b><br>{fmt_pct(mapped_share)} of rows carry a non-unknown cleaned market; '
        f'{mapping["review_pending_labels"]:,} low-volume labels remain queued for manual review. '
        "Market Demand uses conservative cleaned-label aggregates and never infers restaurant-level supply.</div>",
        unsafe_allow_html=True,
    )


def render_cuisines(data: dict, market: str, period: str) -> None:
    hero("Cuisine gaps", "", data)
    st.caption(
        f"Cuisine metrics use the included analytical scope: Order Value ≤ ₹{data['cleaning']['max_order_value_inr']:,}."
    )
    view = data["cuisine_views"][period]
    scoped_pairs = view["pairs"] if market == "All markets" else [row for row in view["pairs"] if row["market"] == market]
    if view["empty"] or not scoped_pairs:
        st.warning("No cuisine opportunity evidence is available for this selection.")
        return

    mapping = data["cuisine_mapping"]
    scope_token = f"{market}|{period}"
    if st.session_state.get("pl_cuisine_scope_previous") != scope_token:
        st.session_state["pl_cuisine_scope_previous"] = scope_token
        st.session_state["pl_selected_cuisine"] = ""
    minimum = st.slider(
        "Minimum allocated transactions",
        min_value=50,
        max_value=500,
        step=50,
        key="pl_cuisine_minimum",
        help="A cuisine-market pair must also have at least half this volume (with a 25-transaction floor) in the previous comparable window.",
    )
    comparison_minimum = max(25, minimum / 2)
    eligible = eligible_cuisine_pairs(scoped_pairs, minimum, 25)

    sort_options = {
        "Rank by opportunity signal": "opportunity_score",
        "Rank by demand": "allocated_orders",
        "Rank by growth": "growth",
        "Rank by demand/listing index": "demand_to_listing_index",
    }
    sort_label = st.selectbox("Rank opportunities by", list(sort_options), key="pl_cuisine_sort")
    sort_field = sort_options[sort_label]
    if st.session_state.get("pl_cuisine_sort_previous") != sort_label:
        st.session_state["pl_cuisine_sort_previous"] = sort_label
        st.session_state["pl_selected_cuisine"] = ""
    ranked = sorted(
        eligible,
        key=lambda row: (
            -(row.get(sort_field) if row.get(sort_field) is not None else float("-inf")),
            str(row.get("market", "")),
            str(row.get("cuisine", "")),
        ),
    )

    ranked_keys = {(row["market"], row["cuisine"]) for row in ranked}
    remaining_rows = sorted(
        [row for row in scoped_pairs if (row["market"], row["cuisine"]) not in ranked_keys],
        key=lambda row: (-row.get("allocated_orders", 0), row.get("market", ""), row.get("cuisine", "")),
    )
    # Keep every scoped pair available for diagnosis, including pairs that are
    # below the active evidence threshold (the reference heatmap can inspect
    # those cells), while placing the ranked queue first for a useful default.
    selection_rows = ranked + remaining_rows
    option_labels = [f'{row["market"]} · {row["cuisine"]}' for row in selection_rows]
    if st.session_state.get("pl_selected_cuisine") not in option_labels:
        st.session_state["pl_selected_cuisine"] = option_labels[0]
    selected_label = st.selectbox("Selected opportunity", option_labels, key="pl_selected_cuisine")
    selected = next(
        row for row in selection_rows if f'{row["market"]} · {row["cuisine"]}' == selected_label
    )

    summary_rows = view.get("cuisines", []) if market == "All markets" else sorted(
        [
            {
                "cuisine": row["cuisine"],
                "allocated_orders": row["allocated_orders"],
                "allocated_sales": row["allocated_sales"],
                "customers": row["customers"],
                "markets": 1,
                "observed_listings": row["observed_listings"],
            }
            for row in scoped_pairs
        ],
        key=lambda row: (-row["allocated_orders"], row["cuisine"]),
    )
    top_cuisine = summary_rows[0] if summary_rows else None
    top_opportunity = max(eligible, key=lambda row: row.get("opportunity_score", float("-inf")), default=None)

    st.markdown(
        f'<div class="pl-filter-meta"><b>Current comparable window</b> {view["current_window"]} '
        f'&nbsp;·&nbsp; <b>Previous equal-length window</b> {view["comparison_window"]} '
        f'&nbsp;·&nbsp; <b>{len(eligible):,} eligible opportunities</b> at {minimum:,}+ allocated transactions '
        f'&nbsp;·&nbsp; <b>{market if market != "All markets" else "All cleaned markets"}</b></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        f"Each multi-cuisine transaction contributes 1/n. Comparison evidence must reach at least "
        f"{comparison_minimum:,.0f} allocated transactions."
    )

    cols = st.columns(5)
    cols[0].metric("Canonical cuisines", fmt_int(mapping["canonical_cuisines"]), f'{mapping["raw_tokens"]:,} raw tokens reviewed')
    cols[1].metric(
        "Highest observed demand",
        top_cuisine["cuisine"] if top_cuisine else "—",
        f'{fmt_decimal(top_cuisine["allocated_orders"])} allocated txns' if top_cuisine else "No evidence",
    )
    cols[2].metric("Eligible opportunities", fmt_int(len(eligible)), f"{minimum:,}+ allocated transactions")
    cols[3].metric(
        "Top opportunity signal",
        f'{top_opportunity["market"]} · {top_opportunity["cuisine"]}' if top_opportunity else "—",
        f'{top_opportunity["opportunity_score"]:.1f} / 100' if top_opportunity else "Insufficient comparison",
    )
    cols[4].metric("Cuisine field coverage", fmt_pct(mapping["cuisine_coverage"]), f'{mapping["excluded_token_rows"]:,} invalid token rows excluded')

    st.markdown('<span class="pl-section-kicker">Allocated demand</span>', unsafe_allow_html=True)
    st.subheader("Leading cuisine demand")
    st.caption("Additive 1/n allocation · top 10 cuisines in the selected market scope")
    summary_frame = cuisine_summary_frame(summary_rows[:10])
    if not summary_frame.empty:
        summary_frame["Cuisine"] = summary_frame["Cuisine"].fillna("Unknown").astype(str)
        for numeric_column in ["Allocated txns", "Allocated sales", "Customers", "Markets", "Observed listings"]:
            summary_frame[numeric_column] = pd.to_numeric(summary_frame[numeric_column], errors="coerce").fillna(0.0)
    if not summary_frame.empty:
        summary_display = summary_frame[["Cuisine", "Allocated txns", "Allocated sales", "Customers", "Markets", "Observed listings"]]
        demand_data = summary_display.sort_values("Allocated txns", ascending=False).set_index("Cuisine")[["Allocated txns"]]
        render_chart_view(
            None,
            summary_display,
            key="pl_cuisine_demand_view",
            label="Display leading cuisine demand as",
            column_config={
                "Cuisine": st.column_config.TextColumn(width="medium"),
                "Allocated txns": st.column_config.NumberColumn(format="%,.1f", width="medium"),
                "Allocated sales": st.column_config.NumberColumn(format="₹%,.0f", width="medium"),
                "Customers": st.column_config.NumberColumn(format="%,.0f", width="medium"),
                "Markets": st.column_config.NumberColumn(format="%,.0f", width="medium"),
                "Observed listings": st.column_config.NumberColumn(format="%,.0f", width="medium"),
            },
            renderer=lambda: st.bar_chart(
                demand_data,
                horizontal=True,
                sort="-Allocated txns",
                color="#194f46",
                x_label="Cuisine",
                y_label="Allocated transactions",
                width="stretch",
                height=340,
            ),
        )
    else:
        st.info("No cuisine demand values are available for this scope.")

    st.markdown('<span class="pl-section-kicker">Selected signal</span>', unsafe_allow_html=True)
    st.subheader(f'{selected["market"]} · {selected["cuisine"]}')
    st.markdown(
        f'<div class="pl-callout"><b>Recommended investigation</b><br>{selected["recommended_action"]}<br>'
        f'<small>{selected["confidence"]} confidence · A high signal prioritizes investigation; it does not prove unmet supply or causal demand.</small></div>',
        unsafe_allow_html=True,
    )
    detail_cols = st.columns(5)
    detail_cols[0].metric("Opportunity signal", f'{selected["opportunity_score"]:.1f} / 100')
    detail_cols[1].metric("Allocated transaction growth", fmt_signed_pct(selected.get("growth")))
    detail_cols[2].metric("Customer reach", fmt_int(selected["customers"]))
    detail_cols[3].metric("Observed normalized listings", fmt_int(selected["observed_listings"]))
    detail_cols[4].metric(
        "Demand-to-listing index",
        f'{selected["demand_to_listing_index"]:.2f}×' if selected.get("demand_to_listing_index") is not None else "—",
    )
    st.caption(f'Rating / menu coverage: {fmt_pct(selected["rating_coverage"])} / {fmt_pct(selected["menu_coverage"])}')

    st.markdown('<span class="pl-section-kicker">Demand footprint</span>', unsafe_allow_html=True)
    st.subheader("Cuisine-market demand heatmap")
    heatmap = cuisine_heatmap_frame(scoped_pairs)
    if not heatmap.empty:
        heatmap["Allocated txns"] = pd.to_numeric(heatmap["Allocated txns"], errors="coerce").fillna(0.0)
        heatmap_chart = (
            alt.Chart(heatmap)
            .mark_rect(stroke="#fffdf8", strokeWidth=1)
            .encode(
                x=alt.X("Cuisine:N", title=None, sort=list(dict.fromkeys(heatmap["Cuisine"]))),
                y=alt.Y("Market:N", title=None, sort=list(dict.fromkeys(heatmap["Market"]))),
                color=alt.Color(
                    "Allocated txns:Q",
                    title="Allocated txns",
                    scale=alt.Scale(scheme="orangered"),
                ),
                tooltip=[
                    alt.Tooltip("Market:N", title="Market"),
                    alt.Tooltip("Cuisine:N", title="Cuisine"),
                    alt.Tooltip("Allocated txns:Q", title="Allocated transactions", format=",.1f"),
                ],
            )
            .properties(height=300)
            .configure_view(stroke=None)
            .configure_axis(labelAngle=-35, gridColor="#e2ded3", titleColor="#65716d", labelColor="#65716d")
        )
        render_chart_view(
            heatmap_chart,
            heatmap,
            key="pl_cuisine_heatmap_view",
            label="Display cuisine-market demand as",
            column_config={
                "Market": st.column_config.TextColumn(width="medium"),
                "Cuisine": st.column_config.TextColumn(width="medium"),
                "Allocated txns": st.column_config.NumberColumn(format="%,.1f", width="medium"),
            },
        )
        st.caption("Top seven markets × top eight cuisines. Darker cells represent greater proportionally allocated demand; use Selected opportunity above to inspect a pair.")

    st.markdown('<span class="pl-section-kicker">Category action queue</span>', unsafe_allow_html=True)
    st.subheader("Eligible cuisine-market opportunities")
    if ranked:
        table = cuisine_ranking_frame(ranked)
        st.dataframe(
            table,
            width="stretch",
            hide_index=True,
            column_config={
                "Market · Cuisine": st.column_config.TextColumn(width="medium"),
                "Signal": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
                "Allocated txns": st.column_config.NumberColumn(format="%,.1f", width="medium"),
                "Growth": st.column_config.NumberColumn(format="+.1f%", width="medium"),
                "Customers": st.column_config.NumberColumn(format="%,.0f", width="medium"),
                "Listings": st.column_config.NumberColumn(format="%,.0f", width="medium"),
                "Demand / listing": st.column_config.NumberColumn(format="%.2f×", width="medium"),
                "Rating cov.": st.column_config.NumberColumn(format="percent", width="medium"),
                "Menu cov.": st.column_config.NumberColumn(format="percent", width="medium"),
                "Confidence": st.column_config.TextColumn(width="medium"),
                "Recommended action": st.column_config.TextColumn(width="large", help="Recommended validation step for the selected evidence signal."),
            },
        )
        st.download_button(
            "Export cuisine evidence",
            table.to_csv(index=False).encode("utf-8"),
            f"dinescope-cuisine-opportunities-{period}.csv",
            "text/csv",
            key="pl_cuisine_export",
        )
    else:
        st.info("No cuisine-market pair clears the current transaction and comparison evidence thresholds.")

    allocation_total = view.get("allocated_order_total")
    covered_orders = view.get("covered_order_count")
    if allocation_total is not None and covered_orders is not None:
        st.markdown(
            f'<div class="pl-note"><b>Allocation reconciliation</b><br>{allocation_total:,.1f} allocated transactions across '
            f'{covered_orders:,} cuisine-covered included orders. Every covered order contributes exactly 1.0 across its observed cuisines.</div>',
            unsafe_allow_html=True,
        )

    restaurant_mapping = data["restaurant_mapping"]
    st.markdown('<span class="pl-section-kicker">Restaurant identity audit</span>', unsafe_allow_html=True)
    st.subheader("Conservative name normalization")
    st.markdown(
        f'<div class="pl-note"><b>{restaurant_mapping["raw_names"]:,}</b> raw names · '
        f'<b>{restaurant_mapping["normalized_names"]:,}</b> normalized names · '
        f'<b>{restaurant_mapping["repeat_normalized_names"]:,}</b> repeated normalized names · '
        f'<b>{restaurant_mapping["restaurant_ids_repeated"]:,}</b> repeated restaurant IDs<br>'
        'Normalization standardizes case, punctuation, accents and “&amp;”. It does not remove outlet locations or fuzzy-merge brands, protecting against false chain matches.</div>',
        unsafe_allow_html=True,
    )
    observations = restaurant_observation_frame(data["restaurant_observations"])
    st.markdown('<span class="pl-section-kicker">Coverage context</span>', unsafe_allow_html=True)
    st.subheader("Most-observed normalized names")
    st.dataframe(
        observations,
        width="stretch",
        hide_index=True,
        column_config={
            "Normalized name": st.column_config.TextColumn(width="large"),
            "Observed rows": st.column_config.NumberColumn(format="%,.0f"),
            "Distinct IDs": st.column_config.NumberColumn(format="%,.0f"),
            "Markets": st.column_config.NumberColumn(format="%,.0f"),
            "Rating coverage": st.column_config.NumberColumn(format="percent"),
            "Menu coverage": st.column_config.NumberColumn(format="percent"),
        },
    )
    st.markdown(
        f'<div class="pl-note"><b>Analytical boundary</b><br>“Observed listings” uses conservative normalized restaurant names—not durable outlet supply. '
        f'Restaurant performance is intentionally not ranked because only {restaurant_mapping["restaurant_ids_repeated"]:,} restaurant IDs repeat.</div>',
        unsafe_allow_html=True,
    )


def render_decision_lab(data: dict, market: str, period: str) -> None:
    hero("Decision lab", "", data)
    st.caption(
        f"Decision Lab uses the included analytical scope: Order Value ≤ ₹{data['cleaning']['max_order_value_inr']:,}."
    )
    view = data["cuisine_views"][period]
    pairs = view["pairs"] if market == "All markets" else [row for row in view["pairs"] if row["market"] == market]
    if view["empty"] or not pairs:
        st.warning("No comparable cuisine evidence is available for this selection.")
        return

    # Controls are namespaced and live only in Streamlit session state. They
    # intentionally do not write to a database or imply durable team sharing.
    scenarios = list(st.session_state.get("pl_decision_scenarios", []))
    if not scenarios:
        scenarios = [{**BASE_DECISION_SCENARIO, "weights": BASE_DECISION_SCENARIO["weights"].copy()}]
        st.session_state["pl_decision_scenarios"] = scenarios

    minimum = st.slider(
        "Minimum allocated transactions",
        min_value=50,
        max_value=500,
        step=50,
        key="pl_decision_minimum",
        help="A pair must also have at least half this volume (with a 25-transaction floor) in the previous comparable window.",
    )
    confidence_discount = st.toggle(
        "Apply confidence discount",
        key="pl_decision_confidence_discount",
        help="Medium evidence ×0.85; low evidence ×0.65.",
    )

    left, right = st.columns([1.25, 1])
    with left:
        st.markdown('<span class="pl-section-kicker">Configurable score</span>', unsafe_allow_html=True)
        st.subheader("What should matter most?")
        weights = {}
        for key, default in DEFAULT_WEIGHTS.items():
            weights[key] = st.slider(
                f"{DECISION_WEIGHT_LABELS[key]} weight",
                min_value=0,
                max_value=50,
                step=5,
                key=f"pl_decision_weight_{key}",
                help=DECISION_WEIGHT_HELP[key],
            )
        weight_total = sum(weights.values())
        st.metric("Weight total", f"{weight_total}%", "normalized to 100% for calculation")
        st.caption("Weights are normalized to 100% for calculation; changing the total never changes the underlying source metrics.")
    with right:
        st.markdown('<span class="pl-section-kicker">Evidence guardrails</span>', unsafe_allow_html=True)
        st.subheader("Keep the ranking defensible")
        st.caption(f"Comparison evidence must reach at least {max(25, minimum / 2):,.0f} allocated transactions.")
        st.markdown(
            '<div class="pl-note"><b>Confidence adjustment</b><br>High evidence is unchanged; Medium is multiplied by 0.85; Low by 0.65.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="pl-note"><b>Current scope</b><br>{view["current_window"]} versus {view["comparison_window"]}<br>'
            f'{market if market != "All markets" else "All cleaned markets"} · {len(pairs):,} cuisine-market signals</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<span class="pl-section-kicker">Saved presets</span>', unsafe_allow_html=True)
    st.subheader("Scenario library")
    st.caption("Stored in this Streamlit session only; scenarios are not server-backed or shared with other users.")
    input_col, save_col = st.columns([3, 1])
    with input_col:
        st.text_input("Scenario name", placeholder="Name this weighting", max_chars=40, key="pl_decision_scenario_name")
    with save_col:
        st.write("")
        st.button(
            "Save scenario",
            key="pl_decision_save_scenario",
            disabled=not str(st.session_state.get("pl_decision_scenario_name", "")).strip(),
            on_click=save_decision_scenario,
        )

    scenario_cols = st.columns(min(max(len(scenarios), 1), 3))
    for index, scenario in enumerate(scenarios):
        with scenario_cols[index % len(scenario_cols)]:
            selected = scenario.get("name") == st.session_state.get(
                "pl_decision_comparison_name", BASE_DECISION_SCENARIO["name"]
            )
            badge = " · comparison" if selected else ""
            st.markdown(
                f'<div class="pl-note"><b>{scenario.get("name", "Unnamed scenario")}</b>{badge}<br>'
                f'<small>{scenario_summary(scenario)} · {"confidence adjusted" if scenario.get("confidence_discount", True) else "no discount"}</small></div>',
                unsafe_allow_html=True,
            )
            action_cols = st.columns(2 if scenario.get("id") != BASE_DECISION_SCENARIO["id"] else 1)
            with action_cols[0]:
                st.button(
                    "Load",
                    key=f'pl_decision_load_{scenario.get("id")}',
                    on_click=load_decision_scenario,
                    args=(scenario,),
                )
            if scenario.get("id") != BASE_DECISION_SCENARIO["id"]:
                with action_cols[1]:
                    st.button(
                        "Remove",
                        key=f'pl_decision_remove_{scenario.get("id")}',
                        on_click=remove_decision_scenario,
                        args=(scenario.get("id"),),
                    )

    current_rows = score_decision_pairs(pairs, minimum, weights, confidence_discount)
    baseline_rows = score_decision_pairs(pairs, minimum, DEFAULT_WEIGHTS, True)
    ranked_rows = add_rank_movement(current_rows, baseline_rows)
    top = ranked_rows[0] if ranked_rows else None
    baseline_top = baseline_rows[0] if baseline_rows else None

    scenario_names = [scenario.get("name", "Unnamed scenario") for scenario in scenarios]
    comparison_name = st.session_state.get("pl_decision_comparison_name", BASE_DECISION_SCENARIO["name"])
    if comparison_name not in scenario_names:
        comparison_name = scenario_names[0]
        st.session_state["pl_decision_comparison_name"] = comparison_name
    comparison_name = st.selectbox("Compare current lab with", scenario_names, key="pl_decision_comparison_name")
    comparison_scenario = next(scenario for scenario in scenarios if scenario.get("name") == comparison_name)
    st.session_state["pl_decision_comparison_id"] = comparison_scenario.get("id", "balanced")
    comparison_rows = score_decision_pairs(
        pairs,
        minimum,
        comparison_scenario.get("weights", DEFAULT_WEIGHTS),
        bool(comparison_scenario.get("confidence_discount", True)),
    )
    comparison_top = comparison_rows[0] if comparison_rows else None
    same_leader = bool(top and comparison_top and decision_row_key(top) == decision_row_key(comparison_top))

    leader_label = f'{top["market"]} · {top["cuisine"]}' if top else "No pair clears the selected evidence threshold."
    leader_score = f'{top["lab_score"]:.1f} / 100' if top else "Use a broader filter or lower threshold."
    baseline_leader_label = f'{baseline_top["market"]} · {baseline_top["cuisine"]}' if baseline_top else "not available"

    st.markdown('<span class="pl-section-kicker">Live scoring sandbox</span>', unsafe_allow_html=True)
    st.subheader("Make the trade-offs explicit")
    st.markdown(
        f'<div class="pl-note"><b>Current lab leader</b><br>{leader_label}'
        f'<br><small>{leader_score} · Every score is relative within the selected evidence base.</small></div>',
        unsafe_allow_html=True,
    )
    compare_cols = st.columns(3)
    compare_cols[0].metric("Current investigation lead", f'{top["market"]} · {top["cuisine"]}' if top else "—")
    compare_cols[1].metric("Lab score", f'{top["lab_score"]:.1f} / 100' if top else "—")
    compare_cols[2].metric("Eligible evidence", f"{len(ranked_rows):,} pairs")

    st.markdown('<span class="pl-section-kicker">Scenario comparison</span>', unsafe_allow_html=True)
    st.subheader("See what the weighting changes")
    comparison_cols = st.columns(3)
    comparison_cols[0].metric(
        "Current lab",
        f'{top["market"]} · {top["cuisine"]}' if top else "—",
        f'{top["lab_score"]:.1f} / 100' if top else "No eligible evidence",
    )
    comparison_cols[1].metric(
        comparison_scenario.get("name", "Scenario"),
        f'{comparison_top["market"]} · {comparison_top["cuisine"]}' if comparison_top else "—",
        f'{comparison_top["lab_score"]:.1f} / 100' if comparison_top else "No eligible evidence",
    )
    comparison_cols[2].metric("Leader stability", "Stable" if same_leader else "Changes", "compare rank movement before acting")
    st.markdown(
        f'<div class="pl-callout"><b>{"Leader is stable under both scenarios." if same_leader else "Leader changes under this scenario."}</b><br>'
        f'{"Balanced baseline leads with " + baseline_leader_label + "; use the movement column to see what changed." if baseline_top else "Use a broader filter or lower threshold to create a comparable evidence base."}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<span class="pl-section-kicker">Decision brief</span>', unsafe_allow_html=True)
    st.subheader("Ranked investigation queue")
    frame = decision_frame(ranked_rows)
    if frame.empty:
        st.info("No pair clears the selected evidence threshold. Lower the threshold only when the resulting evidence remains appropriate for the decision.")
    else:
        st.dataframe(
            frame.head(25),
            width="stretch",
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn(format="%,.0f", width="small"),
                "Market": st.column_config.TextColumn(width="medium"),
                "Cuisine": st.column_config.TextColumn(width="medium"),
                "Lab score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f", width="medium"),
                "Baseline rank": st.column_config.NumberColumn(format="%,.0f", width="small"),
                "Move": st.column_config.TextColumn(width="small"),
                "Demand": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Growth": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Reach": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Gap": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Quality": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "Allocated transactions": st.column_config.NumberColumn(format="%,.1f"),
                "Transaction growth": st.column_config.NumberColumn(format="+.1f%"),
                "Observed listings": st.column_config.NumberColumn(format="%,.0f"),
                "Recommended next action": st.column_config.TextColumn(width="large", help="Recommended validation step for the ranked opportunity."),
            },
        )
        if len(frame) > 25:
            st.caption(f"Showing the top 25 of {len(frame):,} eligible pairs. Export the brief for the full ranked queue.")

    weight_formula = " · ".join(f'{DECISION_WEIGHT_LABELS[key]} {weights[key]}%' for key in DEFAULT_WEIGHTS)
    export_metadata = (
        f"# scope={market}\n# period={period}\n# minimum_allocated_transactions={minimum}\n"
        f"# confidence_discount={'on' if confidence_discount else 'off'}\n# weights={scenario_summary({'weights': weights})}\n"
    )
    st.download_button(
        "Export decision brief",
        (export_metadata + frame.to_csv(index=False)).encode("utf-8"),
        f"dinescope-decision-brief-{market}-{period}.csv".replace(" ", "-").lower(),
        "text/csv",
        key="pl_decision_export",
    )

    st.markdown(
        f'<div class="pl-note"><b>Score formula</b><br>{weight_formula}<br>'
        f'<small>Weights are normalized to 100% for calculation. Confidence adjustment: {"on" if confidence_discount else "off"}.</small></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="pl-callout"><b>Prioritisation is not proof</b><br>The score is a transparent relative ranking for Product, Growth and Category teams. It does not forecast demand, prove unmet supply, or replace restaurant-level validation. Rating/menu coverage and conservative observed-listing context remain part of the evidence boundary.</div>',
        unsafe_allow_html=True,
    )


def render_reliability(data: dict) -> None:
    hero("Data reliability", "", data)
    quality = data["quality"]
    cleaning = data["cleaning"]
    source = data["source"]
    cols = st.columns(5)
    cols[0].metric("Source-valid rate", fmt_pct(quality["valid_rate"]), f'{quality["valid_transactions"]:,} rows pass source checks')
    cols[1].metric("Analysis retention", fmt_pct(cleaning["analysis_retention_rate"]), f'{cleaning["analysis_transactions"]:,} included orders')
    cols[2].metric("Rating coverage", fmt_pct(quality["rating_coverage"]), "Never imputed")
    cols[3].metric("Menu coverage", fmt_pct(quality["menu_coverage"]), "Low-confidence analysis")
    schema_value = f'{source["columns"]} / {source["expected_columns"]}'
    cols[4].metric("Schema integrity", schema_value, f'{quality["duplicate_order_ids"]} duplicate order IDs')

    st.markdown('<span class="pl-section-kicker">Audit trail</span>', unsafe_allow_html=True)
    st.subheader("Transaction reconciliation")
    st.markdown(
        f'<div class="pl-note"><b>{quality["raw_rows"]:,} raw rows − {quality["excluded_transactions"]:,} source-invalid rows '
        f'= {quality["valid_transactions"]:,} source-valid rows</b><br>'
        f'<b>{quality["valid_transactions"]:,} source-valid rows − {cleaning["high_value_excluded_transactions"]:,} '
        f'Order Value exclusions = {cleaning["analysis_transactions"]:,} included analytical transactions</b><br>'
        f'<small>Source-valid sales {fmt_inr(cleaning["source_valid_sales"])} − excluded high-value sales '
        f'{fmt_inr(cleaning["high_value_excluded_sales"])} = filtered sales {fmt_inr(cleaning["analysis_sales"])}. '
        'The original source remains unchanged.</small></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="pl-callout"><b>Two-stage inclusion rule</b><p><b>Source-valid:</b> Order ID present · MM/DD/YYYY date parses · source flag true · sales &gt; 0 · currency = INR.<br>'
        f'<b>Included analytical order:</b> source-valid and Order Value ≤ ₹{cleaning["max_order_value_inr"]:,}. Values above the cutoff remain in the local exclusion audit.</p></div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.15, 1])
    with left:
        st.markdown('<span class="pl-section-kicker">Coverage</span>', unsafe_allow_html=True)
        st.subheader("Observed field coverage")
        coverage = pd.DataFrame(
            {
                "Metric": ["Rating coverage", "Menu coverage", "Restaurant match", "Cuisine mapping"],
                "Coverage": [
                    quality["rating_coverage"],
                    quality["menu_coverage"],
                    quality["restaurant_match_rate"],
                    data["cuisine_mapping"]["cuisine_coverage"],
                ],
            }
        )
        coverage_chart = (
            alt.Chart(coverage)
            .mark_bar(color="#194f46", cornerRadiusEnd=5)
            .encode(
                y=alt.Y("Metric:N", sort=None, title=None),
                x=alt.X("Coverage:Q", title="Coverage", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%")),
                tooltip=[alt.Tooltip("Metric:N", title="Metric"), alt.Tooltip("Coverage:Q", title="Coverage", format=".1%")],
            )
            .properties(height=220)
            .configure_view(stroke=None)
            .configure_axis(gridColor="#e2ded3", titleColor="#65716d", labelColor="#65716d")
        )
        render_chart_view(
            coverage_chart,
            coverage,
            key="pl_reliability_coverage_view",
            label="Display field coverage as",
            column_config={
                "Metric": st.column_config.TextColumn(width="medium"),
                "Coverage": st.column_config.NumberColumn(format="percent", width="medium"),
            },
        )
        st.caption("Coverage is descriptive. Missing fields are never imputed into opportunity metrics.")
    with right:
        st.markdown('<span class="pl-section-kicker">Source fingerprint</span>', unsafe_allow_html=True)
        st.subheader(source["filename"])
        st.markdown(
            f'<div class="pl-note"><b>Rows</b> {source["rows"]:,} · <b>Columns</b> {source["columns"]}<br>'
            f'<b>Date window</b> {source["date_min"]} — {source["date_max"]}<br><b>Date format</b> {source["date_format"]}<br>'
            f'<b>Aggregate</b> {data["aggregate_version"]}<br><b>Order-value cutoff</b> ₹{cleaning["max_order_value_inr"]:,}<br>'
            f'<b>Market mapping</b> {data["location_mapping"]["mapped_rows"]:,} mapped · '
            f'{data["location_mapping"]["unknown_rows"]:,} unknown · {data["location_mapping"]["high_confidence_rows"]:,} high-confidence</div>',
            unsafe_allow_html=True,
        )
        st.caption("Full source checksum (SHA-256)")
        st.code(source["sha256"], language="text")

    issues = pd.DataFrame(reliability_issue_rows(data))
    issues = issues[["Issue", "Affected rows", "Sales impact (INR)", "Severity", "Treatment"]].rename(columns={"Treatment": "Implemented treatment"})
    st.markdown('<span class="pl-section-kicker">Known limitations</span>', unsafe_allow_html=True)
    st.subheader("Quality issues and metric treatment")
    st.dataframe(
        issues,
        width="stretch",
        hide_index=True,
        column_config={
            "Affected rows": st.column_config.NumberColumn(format="%,.0f"),
            "Sales impact (INR)": st.column_config.NumberColumn(format="₹%,.0f"),
        },
    )
    with st.expander("Responsible analytics boundary"):
        st.write("No delivery-time, cancellation, discount, payment, commission, funnel or campaign metrics are shown because those fields do not exist in the source. Demographic differences are descriptive only—not causal targeting recommendations. The public repository contains the derived aggregate, never the raw order-level dataset.")


inject_styles()
data = analytics(hashlib.sha256(DATA_PATH.read_bytes()).hexdigest())
initialise_session_state(data)
flags = parse_feature_flags()
render_topbar(data, flags)
page = render_sidebar(data, flags)
market, period = render_global_filters(data, page)

if st.session_state.pop("pl_methodology_open", False):
    show_methodology(data)

renderers = {
    "Overview": lambda: render_overview(data, market, period),
    "Customer growth": lambda: render_customers(data, market, period),
    "Market demand": lambda: render_markets(data, market, period),
    "Cuisine gaps": lambda: render_cuisines(data, market, period),
    "Decision lab": lambda: render_decision_lab(data, market, period),
    "Data reliability": lambda: render_reliability(data),
}
if not flags.get("shell_v2", True):
    st.warning("The Phase 1 shell is disabled by `DINESCOPE_FEATURE_FLAGS`; the workspace is shown for validation only.")
elif not flags.get(PAGE_FEATURE_FLAGS[page], True):
    st.info(f"{PAGE_COPY[page]['title']} is staged for private validation and is not enabled in this deployment.")
else:
    renderers[page]()
