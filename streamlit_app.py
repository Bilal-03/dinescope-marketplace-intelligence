"""PlateLens public analytics workspace for Streamlit Community Cloud."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from streamlit_lib import DEFAULT_WEIGHTS, decision_frame, load_analytics, score_decision_pairs, scope_key, valid_data_contract


st.set_page_config(
    page_title="PlateLens · Food delivery intelligence",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner="Loading audited analytics…")
def analytics() -> dict:
    payload = load_analytics()
    if not valid_data_contract(payload):
        raise ValueError("The published analytics artifact does not satisfy the PlateLens data contract.")
    return payload


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root { --ink:#17211f; --muted:#65716d; --paper:#f7f5ef; --card:#fffdf8; --green:#194f46; --mint:#dcece5; --coral:#ef6a50; --amber:#e7a83e; }
        .stApp { background: radial-gradient(circle at 82% 3%, #f3decf 0, transparent 24rem), var(--paper); color:var(--ink); }
        [data-testid="stSidebar"] { background:#123c36; }
        [data-testid="stSidebar"] * { color:#f6f3e9 !important; }
        [data-testid="stSidebar"] [data-baseweb="select"] > div { background:#1c4c44; }
        .block-container { max-width:1480px; padding-top:2.4rem; padding-bottom:4rem; }
        .pl-hero { padding:1.5rem 0 1.2rem; border-bottom:1px solid #d9d6cd; margin-bottom:1.3rem; }
        .pl-kicker { color:var(--coral); font-size:.76rem; font-weight:800; letter-spacing:.15em; text-transform:uppercase; }
        .pl-hero h1 { font-family:Georgia,serif; font-size:clamp(2.2rem,5vw,4.4rem); line-height:.96; letter-spacing:-.045em; margin:.45rem 0 .75rem; color:var(--ink); }
        .pl-hero p { color:var(--muted); font-size:1.05rem; max-width:760px; margin:0; }
        .pl-chip { display:inline-block; background:var(--mint); color:var(--green); padding:.32rem .65rem; border-radius:99px; font-weight:700; font-size:.75rem; margin-top:.9rem; }
        div[data-testid="stMetric"] { background:rgba(255,253,248,.92); border:1px solid #e2ded3; border-radius:16px; padding:1rem 1.05rem; box-shadow:0 10px 26px rgba(36,50,46,.05); min-height:120px; }
        div[data-testid="stMetric"] label { color:var(--muted); font-weight:700; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color:var(--ink); font-family:Georgia,serif; }
        div[data-testid="stDataFrame"], div[data-testid="stTable"], .pl-note, .pl-callout { background:var(--card); border:1px solid #e2ded3; border-radius:14px; overflow:hidden; }
        .pl-note, .pl-callout { padding:1rem 1.15rem; color:var(--muted); }
        .pl-callout { border-left:5px solid var(--coral); }
        .pl-callout b { color:var(--ink); }
        h2, h3 { font-family:Georgia,serif !important; color:var(--ink) !important; letter-spacing:-.02em; }
        .stButton button, .stDownloadButton button { border-radius:99px; border:1px solid var(--green); color:var(--green); font-weight:750; }
        .stButton button:hover, .stDownloadButton button:hover { background:var(--green); color:white; }
        [data-testid="stExpander"] { background:rgba(255,253,248,.72); border-radius:12px; }
        footer { visibility:hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def fmt_int(value: float | int) -> str:
    return f"{value:,.0f}"


def fmt_pct(value: float) -> str:
    return f"{value:.1%}"


def fmt_inr(value: float) -> str:
    if abs(value) >= 10_000_000:
        return f"₹{value / 10_000_000:.1f} Cr"
    if abs(value) >= 100_000:
        return f"₹{value / 100_000:.1f} L"
    return f"₹{value:,.0f}"


def hero(page: str, subtitle: str, data: dict) -> None:
    generated = datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00")).strftime("%d %b %Y")
    st.markdown(
        f'<section class="pl-hero"><span class="pl-kicker">PlateLens · {page}</span><h1>{page}</h1>'
        f'<p>{subtitle}</p><span class="pl-chip">Audited aggregate · refreshed {generated}</span></section>',
        unsafe_allow_html=True,
    )


def scope_payload(data: dict, market: str, period: str) -> dict:
    return data["scopes"][scope_key(market, period)]


def render_overview(data: dict, market: str, period: str) -> None:
    hero("Executive overview", "A decision-ready view of demand, customer health and evidence quality.", data)
    scope = scope_payload(data, market, period)
    if scope["empty"]:
        st.warning("No valid transactions are available for this market and period.")
        return
    metrics = scope["metrics"]
    cols = st.columns(5)
    cols[0].metric("Valid transactions", fmt_int(metrics["valid_transactions"]))
    cols[1].metric("Gross sales", fmt_inr(metrics["gross_sales"]))
    cols[2].metric("Active customers", fmt_int(metrics["active_customers"]))
    cols[3].metric("Repeat rate", fmt_pct(metrics["repeat_rate"]))
    cols[4].metric("Average transaction", fmt_inr(metrics["average_transaction_value"]))
    left, right = st.columns([1.65, 1])
    with left:
        st.subheader("Demand trajectory")
        monthly = pd.DataFrame(scope["monthly"])
        monthly["month"] = pd.to_datetime(monthly["month"])
        st.line_chart(monthly.set_index("month")[["orders", "customers"]], color=["#194f46", "#ef6a50"])
    with right:
        st.subheader("Decision signal")
        insight = scope["insight"]
        st.markdown(
            f'<div class="pl-callout"><b>{insight["headline"]}</b><p>{insight["evidence"]}</p>'
            f'<p><strong>Next move:</strong> {insight["action"]}</p><small>{insight["confidence"]} confidence</small></div>',
            unsafe_allow_html=True,
        )
        st.caption("Descriptive evidence, not a causal claim or forecast.")
    st.subheader("Lifecycle mix")
    segments = pd.DataFrame(scope["segments"])
    display = segments[["segment", "customers", "customer_share", "orders_per_customer", "sales_per_customer", "repeat_rate", "median_recency", "action"]].copy()
    display.columns = ["Segment", "Customers", "Share", "Orders / customer", "Sales / customer", "Repeat rate", "Median recency", "Suggested action"]
    st.dataframe(display, width="stretch", hide_index=True, column_config={"Share": st.column_config.NumberColumn(format="%.1%%"), "Repeat rate": st.column_config.NumberColumn(format="%.1%%"), "Sales / customer": st.column_config.NumberColumn(format="₹%.0f")})


def render_customers(data: dict, market: str, period: str) -> None:
    hero("Customer growth", "Understand acquisition, returning demand, frequency and retention without overstating causality.", data)
    scope = scope_payload(data, market, period)
    if scope["empty"]:
        st.warning("No valid transactions are available for this market and period.")
        return
    metrics = scope["metrics"]
    cols = st.columns(4)
    cols[0].metric("New customers", fmt_int(metrics["new_customers"]))
    cols[1].metric("Repeat customers", fmt_int(metrics["repeat_customers"]))
    cols[2].metric("Orders / customer", f'{metrics["orders_per_customer"]:.2f}')
    cols[3].metric("Repeat rate", fmt_pct(metrics["repeat_rate"]))
    left, right = st.columns([1.55, 1])
    with left:
        st.subheader("New versus returning customers")
        monthly = pd.DataFrame(scope["monthly"])
        monthly["month"] = pd.to_datetime(monthly["month"])
        st.area_chart(monthly.set_index("month")[["new_customers", "returning_customers"]], color=["#ef6a50", "#194f46"])
    with right:
        st.subheader("Observed order frequency")
        frequency = pd.DataFrame(scope["frequency"])
        st.bar_chart(frequency.set_index("frequency")["customers"], color="#e7a83e")
    st.subheader("Six-month cohort retention (%)")
    cohorts = pd.DataFrame({row["cohort"]: row["retention"] for row in scope["cohorts"]}, index=["M0", "M1", "M2", "M3", "M4", "M5", "M6"]).T
    heatmap = cohorts.style.map(lambda value: f"background-color: rgba(25,79,70,{0.08 + min(value, 100) / 125:.2f}); color: {'white' if value >= 55 else '#17211f'}").format("{:.1f}%")
    st.dataframe(heatmap, width="stretch")
    st.markdown('<div class="pl-note"><b>Interpretation boundary</b><br>Repeat rate is the share of active customers with at least two valid transactions in the selected scope. Cohort retention is the stronger view for judging whether acquisition compounds.</div>', unsafe_allow_html=True)


def render_markets(data: dict, market: str, period: str) -> None:
    hero("Market demand", "Compare cleaned markets on scale, growth, value and confidence.", data)
    view = data["market_views"][period]
    rows = view["markets"] if market == "All markets" else [row for row in view["markets"] if row["market"] == market]
    if view["empty"] or not rows:
        st.warning("No comparable market evidence is available for this selection.")
        return
    st.caption(f'{view["current_window"]} versus {view["comparison_window"]} · minimum {view["minimum_orders"]:,} transactions')
    summary = view["summary"]
    cols = st.columns(4)
    cols[0].metric("Active markets", summary["active_markets"])
    cols[1].metric("Largest market", summary["largest_market"], fmt_int(summary["largest_market_orders"]))
    cols[2].metric("Fastest growth", summary["fastest_growth_market"] or "—", fmt_pct(summary["fastest_growth_rate"]) if summary["fastest_growth_rate"] is not None else None)
    cols[3].metric("Top-five concentration", fmt_pct(summary["top_five_concentration"]))
    frame = pd.DataFrame(rows)
    st.subheader("Scale and momentum")
    st.scatter_chart(frame, x="orders", y="growth_orders", size="sales", color="confidence", width="stretch")
    table = frame[["market", "orders", "sales", "customers", "repeat_rate", "average_transaction_value", "growth_orders", "growth_sales", "mapping_confidence", "confidence"]].copy()
    table.columns = ["Market", "Transactions", "Sales", "Customers", "Repeat rate", "Average transaction", "Transaction growth", "Sales growth", "Mapping confidence", "Confidence"]
    st.dataframe(table, width="stretch", hide_index=True, column_config={"Sales": st.column_config.NumberColumn(format="₹%.0f"), "Average transaction": st.column_config.NumberColumn(format="₹%.0f"), "Repeat rate": st.column_config.NumberColumn(format="%.1%%"), "Transaction growth": st.column_config.NumberColumn(format="%.1%%"), "Sales growth": st.column_config.NumberColumn(format="%.1%%"), "Mapping confidence": st.column_config.NumberColumn(format="%.1%%")})
    st.download_button("Download market evidence", table.to_csv(index=False).encode(), f"platelens-markets-{period}.csv", "text/csv")


def render_cuisines(data: dict, market: str, period: str) -> None:
    hero("Cuisine opportunity", "Prioritise market–cuisine investigations using allocated demand, coverage context and explicit evidence limits.", data)
    view = data["cuisine_views"][period]
    pairs = view["pairs"] if market == "All markets" else [row for row in view["pairs"] if row["market"] == market]
    if view["empty"] or not pairs:
        st.warning("No cuisine opportunity evidence is available for this selection.")
        return
    minimum = st.slider("Minimum allocated transactions", 50, 500, int(view.get("minimum_allocated_orders", 100)), 50)
    eligible = [row for row in pairs if row["allocated_orders"] >= minimum and row["previous_allocated_orders"] >= max(25, minimum / 2) and row["growth"] is not None]
    eligible.sort(key=lambda row: (-row["opportunity_score"], -row["allocated_orders"]))
    top = eligible[0] if eligible else None
    cols = st.columns(4)
    cols[0].metric("Eligible pairs", fmt_int(len(eligible)))
    cols[1].metric("Highest observed demand", view["summary"]["top_cuisine"] or "—")
    cols[2].metric("Top opportunity", f'{top["market"]} · {top["cuisine"]}' if top else "—")
    cols[3].metric("Opportunity signal", f'{top["opportunity_score"]:.1f} / 100' if top else "—")
    if eligible:
        frame = pd.DataFrame(eligible)
        st.subheader("Category action queue")
        table = frame[["market", "cuisine", "opportunity_score", "allocated_orders", "growth", "customers", "observed_listings", "demand_to_listing_index", "rating_coverage", "menu_coverage", "confidence", "recommended_action"]].copy()
        table.columns = ["Market", "Cuisine", "Signal", "Allocated transactions", "Growth", "Customers", "Listings", "Demand / listing", "Rating coverage", "Menu coverage", "Confidence", "Recommended action"]
        st.dataframe(table.head(100), width="stretch", hide_index=True, column_config={"Signal": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"), "Growth": st.column_config.NumberColumn(format="%.1%%"), "Rating coverage": st.column_config.NumberColumn(format="%.1%%"), "Menu coverage": st.column_config.NumberColumn(format="%.1%%")})
        st.download_button("Download cuisine evidence", table.to_csv(index=False).encode(), f"platelens-cuisines-{period}.csv", "text/csv")
    st.markdown('<div class="pl-note"><b>Method</b><br>Multi-cuisine transactions use additive 1/n allocation. The opportunity signal is descriptive and confidence-adjusted; it does not prove unmet supply or individual restaurant performance.</div>', unsafe_allow_html=True)


def render_decision_lab(data: dict, market: str, period: str) -> None:
    hero("Decision Lab", "Make prioritisation trade-offs explicit with adjustable weights and evidence guardrails.", data)
    view = data["cuisine_views"][period]
    pairs = view["pairs"] if market == "All markets" else [row for row in view["pairs"] if row["market"] == market]
    if view["empty"] or not pairs:
        st.warning("No comparable cuisine evidence is available for this selection.")
        return
    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("What should matter most?")
        weights = {}
        labels = {"demand": "Demand scale", "growth": "Growth momentum", "reach": "Customer reach", "gap": "Coverage gap", "quality": "Data quality"}
        for key, default in DEFAULT_WEIGHTS.items():
            weights[key] = st.slider(labels[key], 0, 50, default, 5, key=f"decision-{key}")
    with right:
        st.subheader("Evidence guardrails")
        minimum = st.slider("Minimum allocated transactions", 50, 500, 100, 50, key="decision-minimum")
        confidence_discount = st.toggle("Apply confidence discount", True, help="Medium evidence ×0.85; low evidence ×0.65.")
        st.metric("Weight total", f"{sum(weights.values())}%", "normalized to 100% for scoring")
        st.caption(f"Comparison evidence must reach at least {max(25, minimum / 2):,.0f} allocated transactions.")
    rows = score_decision_pairs(pairs, minimum, weights, confidence_discount)
    if not rows:
        st.warning("No pair clears the current evidence threshold.")
        return
    top = rows[0]
    cols = st.columns(3)
    cols[0].metric("Current investigation lead", f'{top["market"]} · {top["cuisine"]}')
    cols[1].metric("Lab score", f'{top["lab_score"]:.1f} / 100')
    cols[2].metric("Eligible evidence", f"{len(rows):,} pairs")
    frame = decision_frame(rows)
    st.subheader("Ranked investigation queue")
    st.dataframe(frame.head(50), width="stretch", hide_index=True, column_config={"Lab score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"), "Transaction growth": st.column_config.NumberColumn(format="%.1%%")})
    st.download_button("Download decision brief", frame.to_csv(index=False).encode(), f"platelens-decision-{market}-{period}.csv", "text/csv")
    st.markdown(f'<div class="pl-callout"><b>{top["market"]} · {top["cuisine"]} is the current investigation lead.</b><p>The score is a transparent relative ranking under the active weighting. It is not a forecast, proof of unmet supply, or a replacement for restaurant-level validation.</p></div>', unsafe_allow_html=True)


def render_reliability(data: dict) -> None:
    hero("Data reliability", "See exactly what was accepted, excluded, mapped and left outside the product’s claims.", data)
    quality = data["quality"]
    cols = st.columns(4)
    cols[0].metric("Raw rows", fmt_int(quality["raw_rows"]))
    cols[1].metric("Excluded", fmt_int(quality["excluded_transactions"]))
    cols[2].metric("Valid transactions", fmt_int(quality["valid_transactions"]))
    cols[3].metric("Valid rate", fmt_pct(quality["valid_rate"]))
    st.markdown('<div class="pl-callout"><b>Valid transaction rule</b><p>Order ID present · MM/DD/YYYY date parses · source flag true · sales &gt; 0 · currency = INR.</p></div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        st.subheader("Coverage")
        coverage = pd.DataFrame({"Metric": ["Rating coverage", "Menu coverage", "Restaurant match rate", "Cuisine mapping coverage"], "Coverage": [quality["rating_coverage"], quality["menu_coverage"], quality["restaurant_match_rate"], data["cuisine_mapping"]["cuisine_coverage"]]})
        st.bar_chart(coverage.set_index("Metric"), horizontal=True, color="#194f46")
    with right:
        st.subheader("Source fingerprint")
        source = data["source"]
        st.markdown(f'<div class="pl-note"><b>{source["filename"]}</b><br>{source["rows"]:,} rows · {source["columns"]} columns<br>{source["date_min"]} — {source["date_max"]}<br><small>SHA-256 {source["sha256"][:16]}…</small></div>', unsafe_allow_html=True)
        st.write("")
        st.metric("Mapped market rows", fmt_int(data["location_mapping"]["mapped_rows"]))
    issues = pd.DataFrame([
        ["Zero sales", quality["zero_sales"], "Excluded from transaction metrics"],
        ["Missing sales", quality["missing_sales"], "Excluded from transaction metrics"],
        ["Unsupported currency", quality["unsupported_currency"], "Excluded; INR only"],
        ["Unknown / unmapped market", data["location_mapping"]["unknown_rows"], "Retained in all-market totals; excluded from named-market views"],
        ["Low rating coverage", quality["valid_transactions"] * (1 - quality["rating_coverage"]), "Coverage shown beside opportunity signals"],
        ["Low menu coverage", quality["valid_transactions"] * (1 - quality["menu_coverage"]), "Coverage shown beside opportunity signals"],
    ], columns=["Issue", "Affected rows", "Treatment"])
    st.subheader("Known limitations and treatment")
    st.dataframe(issues, width="stretch", hide_index=True, column_config={"Affected rows": st.column_config.NumberColumn(format="%.0f")})
    with st.expander("Responsible analytics boundary"):
        st.write("No delivery-time, cancellation, discount, payment, commission, funnel or campaign metrics are shown because those fields do not exist in the source. Demographic differences are descriptive only—not causal targeting recommendations. The public repository contains the derived aggregate, never the raw order-level dataset.")


inject_styles()
data = analytics()

with st.sidebar:
    st.markdown("## ◉ PlateLens")
    st.caption("Food delivery market intelligence")
    page = st.radio("Workspace", ["Executive overview", "Customer growth", "Market demand", "Cuisine opportunity", "Decision Lab", "Data reliability"], label_visibility="collapsed")
    st.divider()
    market = st.selectbox("Market", data["filters"]["markets"])
    period = st.selectbox("Period", data["filters"]["periods"])
    st.divider()
    st.caption(f'{data["quality"]["valid_transactions"]:,} audited transactions')
    st.caption("Public read-only analytics · no raw customer records")
    st.markdown("[Source, methods and support](https://github.com/Bilal-03/platelens-food-delivery-intelligence)")
    st.caption("Independent portfolio case study. Not affiliated with or endorsed by Zomato, Swiggy or another food-delivery company.")

renderers = {
    "Executive overview": lambda: render_overview(data, market, period),
    "Customer growth": lambda: render_customers(data, market, period),
    "Market demand": lambda: render_markets(data, market, period),
    "Cuisine opportunity": lambda: render_cuisines(data, market, period),
    "Decision Lab": lambda: render_decision_lab(data, market, period),
    "Data reliability": lambda: render_reliability(data),
}
renderers[page]()
