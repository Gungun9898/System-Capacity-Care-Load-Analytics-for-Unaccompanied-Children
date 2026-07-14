import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "mydb.db"

st.set_page_config(
    page_title="UAC Care System Command Center",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLORS = {
    "blue": "#2563eb",
    "red": "#ef4444",
    "green": "#16a34a",
    "amber": "#d97706",
    "slate": "#334155",
    "muted": "#64748b",
    "purple": "#7c3aed",
}

METRIC_LABELS = {
    "total_system_load": "Total System Load",
    "net_intake_pressure": "Net Intake Pressure",
    "backlog_accumulation_14d": "14-Day Backlog",
    "discharge_offset_ratio": "Discharge Offset Ratio",
    "cbp_apprehended": "CBP Apprehended",
    "cbp_transferred_out": "CBP Transferred Out",
    "hhs_discharged": "HHS Discharged",
    "hhs_care": "HHS Care",
    "cbp_custody": "CBP Custody",
}

RISK_DRIVER_HELP = {
    "Net pressure": "Intake is high compared with transfers and discharges.",
    "Backlog": "The 14-day backlog is high compared with historical levels.",
    "System load": "The current total load is high compared with historical levels.",
    "Low discharge offset": "Discharges are not offsetting intake strongly enough.",
}

TABLE_ALIASES = {
    "report_date": "Report Date",
    "total_system_load": "Total System Load",
    "net_intake_pressure": "Net Intake Pressure",
    "backlog_accumulation_14d": "14-Day Backlog",
    "discharge_offset_ratio": "Discharge Offset Ratio",
    "cbp_apprehended": "CBP Apprehended",
    "cbp_transferred_out": "CBP Transferred Out",
    "hhs_discharged": "HHS Discharged",
    "hhs_care": "HHS Care",
    "cbp_custody": "CBP Custody",
    "z_score": "Anomaly Score",
    "direction": "Direction",
}

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: "Trebuchet MS", "Segoe UI Rounded", "Aptos", "Segoe UI", Arial, sans-serif;
    }
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 14% 16%, rgba(147, 197, 253, 0.55), transparent 28%),
            radial-gradient(circle at 88% 12%, rgba(254, 215, 170, 0.46), transparent 30%),
            radial-gradient(circle at 74% 88%, rgba(187, 247, 208, 0.34), transparent 29%),
            linear-gradient(135deg, #eff6ff 0%, #fff7ed 48%, #f8fafc 100%);
        background-attachment: fixed;
    }
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        opacity: 0.20;
        background-image: url("data:image/svg+xml,%3Csvg width='1060' height='700' viewBox='0 0 1060 700' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='760' y='86' width='190' height='126' rx='26' fill='%23ffffff' stroke='%232563eb' stroke-width='5'/%3E%3Cpath d='M792 170 C818 132 846 164 870 122 C890 88 914 122 934 101' stroke='%2316a34a' stroke-width='8'/%3E%3Ccircle cx='804' cy='126' r='12' fill='%23ef4444' stroke='none'/%3E%3Ccircle cx='900' cy='152' r='10' fill='%23f59e0b' stroke='none'/%3E%3Crect x='74' y='470' width='220' height='138' rx='30' fill='%23ffffff' stroke='%237c3aed' stroke-width='5'/%3E%3Crect x='116' y='538' width='26' height='38' rx='8' fill='%232563eb' stroke='none'/%3E%3Crect x='166' y='506' width='26' height='70' rx='8' fill='%2316a34a' stroke='none'/%3E%3Crect x='216' y='488' width='26' height='88' rx='8' fill='%23ef4444' stroke='none'/%3E%3Ccircle cx='910' cy='512' r='58' fill='%23bfdbfe' stroke='none'/%3E%3Cpath d='M870 518 Q910 456 950 518 Q910 580 870 518Z' fill='%23ffffff' stroke='%232563eb' stroke-width='5'/%3E%3Ccircle cx='910' cy='518' r='14' fill='%232563eb' stroke='none'/%3E%3Cpath d='M506 76 q34 -38 68 0 t68 0' stroke='%23f59e0b' stroke-width='10'/%3E%3C/g%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 34px top 84px;
        background-size: min(1060px, 72vw) auto;
    }
    [data-testid="stAppViewContainer"] > .main {
        position: relative;
        z-index: 1;
    }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1550px; }
    [data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(239, 246, 255, 0.92)),
            radial-gradient(circle at 24% 8%, rgba(147, 197, 253, 0.30), transparent 34%);
        border-right: 1px solid rgba(191, 219, 254, 0.95);
        backdrop-filter: blur(12px);
    }
    h1, h2, h3 {
        letter-spacing: 0;
        font-family: "Trebuchet MS", "Segoe UI Rounded", "Aptos", "Segoe UI", Arial, sans-serif;
        color: #172033;
    }
    h1 { text-shadow: 0 2px 0 rgba(255, 255, 255, 0.78); }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.90);
        border: 1px solid rgba(191, 219, 254, 0.95);
        border-top: 4px solid rgba(37, 99, 235, 0.46);
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 14px 34px rgba(37, 99, 235, 0.10), 0 2px 6px rgba(15, 23, 42, 0.05);
    }
    div[data-testid="stMetricLabel"] p { color: #64748b; font-size: 0.86rem; }
    .section-note { color: #64748b; font-size: 0.96rem; margin-top: -0.65rem; margin-bottom: 1.1rem; }
    .risk-box {
        border: 1px solid rgba(191, 219, 254, 0.95);
        border-radius: 8px;
        padding: 1rem 1.1rem;
        background: rgba(255, 255, 255, 0.90);
        box-shadow: 0 14px 34px rgba(37, 99, 235, 0.10), 0 2px 6px rgba(15, 23, 42, 0.05);
    }
    .risk-label { color: #64748b; font-size: 0.86rem; margin-bottom: 0.25rem; }
    .risk-value { font-size: 2.1rem; line-height: 1; font-weight: 700; color: #0f172a; }
.risk-status { font-size: 1rem; font-weight: 700; margin-top: 0.45rem; }
    .banner {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid rgba(191, 219, 254, 0.95);
        border-left: 5px solid #2563eb;
        border-radius: 8px;
        padding: 1rem 1.15rem;
        margin-bottom: 1rem;
        box-shadow: 0 14px 34px rgba(37, 99, 235, 0.10);
    }
    .banner-title { color: #334155; font-size: 0.9rem; font-weight: 700; margin-bottom: 0.35rem; }
    .banner-value { color: #0f172a; font-size: 1.45rem; font-weight: 700; line-height: 1.2; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading SQLite views...")
def load_data(db_path: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with sqlite3.connect(db_path) as conn:
        df_feed = pd.read_sql("SELECT * FROM vw_uac_dashboard_feed", conn)
        df_kpi = pd.read_sql("SELECT * FROM vw_uac_kpi_daily", conn)
        df_month = pd.read_sql("SELECT * FROM vw_uac_monthly_summary", conn)

    for frame in (df_feed, df_kpi):
        frame["report_date"] = pd.to_datetime(frame["report_date"], errors="coerce")
        frame["year"] = frame["report_date"].dt.year.astype("Int64")
        frame["month"] = frame["report_date"].dt.month.astype("Int64")

    df_month["month_start_date"] = pd.to_datetime(df_month["month_start_date"], errors="coerce")
    df_month["month_end_date"] = pd.to_datetime(df_month["month_end_date"], errors="coerce")
    df_month["year"] = df_month["month_end_date"].dt.year.astype("Int64")
    df_month["month"] = df_month["month_end_date"].dt.month.astype("Int64")
    df_month["month_label"] = df_month["month_end_date"].dt.strftime("%b %Y")

    numeric_cols = [
        "cbp_apprehended", "cbp_custody", "cbp_transferred_out", "hhs_care",
        "hhs_discharged", "total_system_load", "net_intake_pressure",
        "discharge_offset_ratio", "cbp_transfer_to_apprehension_ratio",
        "net_intake_pressure_7d_avg", "total_system_load_7d_avg", "hhs_care_7d_avg",
        "backlog_accumulation_14d", "record_count", "total_cbp_apprehended",
        "avg_cbp_custody", "total_cbp_transferred_out", "avg_hhs_care",
        "total_hhs_discharged", "avg_total_system_load", "total_net_intake_pressure",
        "avg_discharge_offset_ratio",
    ]
    for frame in (df_feed, df_kpi, df_month):
        for col in numeric_cols:
            if col in frame.columns:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")

    return df_feed, df_kpi, df_month


def fmt(value, decimals: int = 0) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:,.{decimals}f}" if decimals else f"{value:,.0f}"


def pct_delta(current, previous) -> str | None:
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return None
    return f"{((current - previous) / abs(previous)) * 100:+.1f}%"


def style_fig(fig: go.Figure, height: int = 390) -> go.Figure:
    fig.update_layout(
        height=height,
        template="plotly_white",
        margin=dict(l=20, r=20, t=58, b=30),
        legend_title_text="",
        hovermode="x unified",
        font=dict(family="Segoe UI, Arial", color="#0f172a"),
        title=dict(font=dict(size=18, color="#0f172a")),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e2e8f0", zerolinecolor="#cbd5e1")
    return fig


def empty(message: str) -> None:
    st.info(message)


def normalize_component(value: float, low: float, high: float, inverse: bool = False) -> float:
    if pd.isna(value) or pd.isna(low) or pd.isna(high) or high == low:
        return 0.0
    raw = (high - value) / (high - low) if inverse else (value - low) / (high - low)
    return float(np.clip(raw * 100, 0, 100))


def score_status(score: float) -> tuple[str, str]:
    if score >= 75:
        return "Critical", COLORS["red"]
    if score >= 55:
        return "Elevated", COLORS["amber"]
    if score >= 35:
        return "Watch", COLORS["blue"]
    return "Stable", COLORS["green"]


def calculate_risk(feed_frame: pd.DataFrame, reference: pd.DataFrame) -> tuple[float, dict[str, float]]:
    if feed_frame.empty:
        return 0.0, {}
    latest = feed_frame.sort_values("report_date").iloc[-1]
    drivers = {
        "Net pressure": normalize_component(latest["net_intake_pressure"], reference["net_intake_pressure"].quantile(0.25), reference["net_intake_pressure"].quantile(0.90)),
        "Backlog": normalize_component(latest["backlog_accumulation_14d"], reference["backlog_accumulation_14d"].quantile(0.25), reference["backlog_accumulation_14d"].quantile(0.90)),
        "System load": normalize_component(latest["total_system_load"], reference["total_system_load"].quantile(0.25), reference["total_system_load"].quantile(0.90)),
        "Low discharge offset": normalize_component(latest["discharge_offset_ratio"], reference["discharge_offset_ratio"].quantile(0.10), reference["discharge_offset_ratio"].quantile(0.75), inverse=True),
    }
    score = drivers["Net pressure"] * 0.35 + drivers["Backlog"] * 0.25 + drivers["System load"] * 0.25 + drivers["Low discharge offset"] * 0.15
    return float(score), drivers


def add_anomaly_columns(df: pd.DataFrame, metric: str, window: int, threshold: float) -> pd.DataFrame:
    result = df.sort_values("report_date").copy()
    min_periods = max(5, window // 2)
    result["rolling_mean"] = result[metric].rolling(window=window, min_periods=min_periods).mean()
    result["rolling_std"] = result[metric].rolling(window=window, min_periods=min_periods).std().replace(0, np.nan)
    result["z_score"] = (result[metric] - result["rolling_mean"]) / result["rolling_std"]
    result["is_anomaly"] = result["z_score"].abs() >= threshold
    result["direction"] = np.where(result["z_score"] >= threshold, "High", "Low")
    return result


def forecast_metric(df: pd.DataFrame, metric: str, horizon: int, lookback: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    history = df.sort_values("report_date")[["report_date", metric]].dropna().tail(lookback).copy()
    if len(history) < 8:
        return history, pd.DataFrame()
    y = history[metric].astype(float).to_numpy()
    x = np.arange(len(history), dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    fitted = intercept + slope * x
    residual_std = float(np.std(y - fitted, ddof=1)) if len(history) > 2 else 0.0
    future_x = np.arange(len(history), len(history) + horizon, dtype=float)
    future_dates = pd.date_range(history["report_date"].max() + pd.Timedelta(days=1), periods=horizon, freq="D")
    predicted = intercept + slope * future_x
    band = 1.96 * residual_std * np.sqrt(np.arange(1, horizon + 1))
    forecast = pd.DataFrame({"report_date": future_dates, "forecast": predicted, "lower": predicted - band, "upper": predicted + band})
    return history, forecast


def aggregate_daily(df: pd.DataFrame, freq_label: str) -> pd.DataFrame:
    if freq_label == "Daily":
        return df.sort_values("report_date")
    rule = "W" if freq_label == "Weekly" else "M"
    return df.sort_values("report_date").set_index("report_date").resample(rule).mean(numeric_only=True).reset_index()


if not DB_PATH.exists():
    st.error(f"Database not found: {DB_PATH}")
    st.stop()

feed_all, kpi_all, month_all = load_data(str(DB_PATH))
years = sorted(int(y) for y in pd.concat([feed_all["year"], kpi_all["year"], month_all["year"]]).dropna().unique())

if not years:
    st.error("No usable dates were found in the three dashboard views.")
    st.stop()

min_date = min(feed_all["report_date"].min(), kpi_all["report_date"].min(), month_all["month_start_date"].min())
max_date = max(feed_all["report_date"].max(), kpi_all["report_date"].max(), month_all["month_end_date"].max())

st.sidebar.title("Filters")
year_options = ["All years"] + years
selected_year_options = st.sidebar.multiselect(
    "Year",
    options=year_options,
    default=["All years"],
    help="Use All years when you want the date range to control the timeline by itself.",
)
use_all_years = "All years" in selected_year_options
selected_years = years if use_all_years else [int(y) for y in selected_year_options if y != "All years"]

if not selected_years:
    st.warning("Select at least one year, or choose All years, to populate the dashboard.")
    st.stop()

frequency = st.sidebar.radio(
    "Trend frequency",
    ["Daily", "Weekly", "Monthly"],
    index=1,
    horizontal=True,
    help="Pick how trends should be grouped before choosing the date range.",
)

date_scope = feed_all[feed_all["year"].isin(selected_years)].copy()
if date_scope.empty:
    st.error("No dates are available for the selected year filter.")
    st.stop()

date_min = date_scope["report_date"].min()
date_max = date_scope["report_date"].max()
date_key_year = "all" if use_all_years else "_".join(str(year) for year in selected_years)
selected_dates = st.sidebar.date_input(
    "Date range",
    value=(date_min.date(), date_max.date()),
    min_value=date_min.date(),
    max_value=date_max.date(),
    key=f"date_range_{date_key_year}_{frequency}",
    help="This range automatically resets to the valid dates for the selected year and trend frequency.",
)

primary_metric = st.sidebar.selectbox(
    "Primary metric",
    options=list(METRIC_LABELS.keys()),
    index=list(METRIC_LABELS.keys()).index("total_system_load"),
    format_func=lambda value: METRIC_LABELS[value],
)

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date = pd.Timestamp(selected_dates[0])
    end_date = pd.Timestamp(selected_dates[1]) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
elif isinstance(selected_dates, tuple) and len(selected_dates) == 1:
    start_date = pd.Timestamp(selected_dates[0])
    end_date = start_date + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
else:
    start_date = pd.Timestamp(selected_dates)
    end_date = start_date + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)

feed = feed_all[feed_all["year"].isin(selected_years) & feed_all["report_date"].between(start_date, end_date)].copy()
kpi = kpi_all[kpi_all["year"].isin(selected_years) & kpi_all["report_date"].between(start_date, end_date)].copy()
month = month_all[month_all["year"].isin(selected_years) & month_all["month_end_date"].between(start_date, end_date)].copy()

selected_year_label = "All years" if use_all_years else ", ".join(str(y) for y in selected_years)
selected_range_label = f"{start_date:%b %d, %Y} to {end_date:%b %d, %Y}"
year_only_feed = feed_all[feed_all["year"].isin(selected_years)].copy()
date_only_feed = feed_all[feed_all["report_date"].between(start_date, end_date)].copy()

risk_score, risk_drivers = calculate_risk(feed, feed_all)
risk_label, risk_color = score_status(risk_score)

st.sidebar.caption(f"Data available: {min_date:%b %d, %Y} to {max_date:%b %d, %Y}")
st.sidebar.divider()
st.sidebar.subheader("Current Selection")
st.sidebar.metric("Daily records", fmt(len(feed)))
st.sidebar.metric("Monthly periods", fmt(len(month)))
st.sidebar.metric("Risk score", f"{risk_score:.0f}/100")
st.sidebar.caption(f"Active years: {selected_year_label}")
st.sidebar.caption("Source views: Dashboard Feed, Daily KPI, Monthly Summary.")

if feed.empty:
    if year_only_feed.empty:
        st.error(f"No daily rows exist for the selected year filter: {selected_year_label}. Choose All years or another year.")
    elif date_only_feed.empty:
        st.error(f"No daily rows exist for the selected date range: {selected_range_label}. Expand the date range.")
    else:
        available_for_years = f"{year_only_feed['report_date'].min():%b %d, %Y} to {year_only_feed['report_date'].max():%b %d, %Y}"
        st.error(
            "The selected year and date range do not overlap. "
            f"For {selected_year_label}, available daily data is {available_for_years}."
        )

st.title("UAC Care System Command Center")
st.markdown('<div class="section-note">Operational view of CBP intake, transfers, HHS care, discharges, system load, risk, anomalies, and forecasted pressure.</div>', unsafe_allow_html=True)

tab_exec, tab_ops, tab_risk, tab_forecast, tab_scenario, tab_data = st.tabs(["Executive Summary", "Operations Monitor", "Backlog & Risk", "Forecast & Anomalies", "Scenario Lab", "Data Quality"])

with tab_exec:
    st.subheader("Executive Summary")
    if feed.empty:
        empty("No daily feed records match the selected filters.")
    else:
        feed_sorted = feed.sort_values("report_date")
        latest = feed_sorted.iloc[-1]
        previous = feed_sorted.iloc[-2] if len(feed_sorted) > 1 else None
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total System Load", fmt(latest["total_system_load"]), pct_delta(latest["total_system_load"], previous["total_system_load"] if previous is not None else pd.NA))
        c2.metric("Net Intake Pressure", fmt(latest["net_intake_pressure"]), pct_delta(latest["net_intake_pressure"], previous["net_intake_pressure"] if previous is not None else pd.NA))
        c3.metric("14-Day Backlog", fmt(latest["backlog_accumulation_14d"]))
        c4.metric("Discharge Offset Ratio", fmt(latest["discharge_offset_ratio"], 2))
        st.caption(f"Latest daily record: {latest['report_date']:%B %d, %Y}")

        risk_col, driver_col = st.columns((0.75, 1.25))
        risk_col.markdown(f"""
            <div class="risk-box">
                <div class="risk-label">Composite Operational Risk</div>
                <div class="risk-value">{risk_score:.0f}/100</div>
                <div class="risk-status" style="color: {risk_color};">{risk_label}</div>
            </div>
            """, unsafe_allow_html=True)
        driver_df = pd.DataFrame({"Driver": list(risk_drivers.keys()), "Contribution": list(risk_drivers.values())}).sort_values("Contribution", ascending=True)
        fig_drivers = px.bar(driver_df, x="Contribution", y="Driver", orientation="h", title="Risk Driver Intensity", range_x=[0, 100], color="Contribution", color_continuous_scale=["#16a34a", "#f59e0b", "#ef4444"])
        driver_col.plotly_chart(style_fig(fig_drivers, 285), use_container_width=True)

    if month.empty:
        empty("No monthly summary records match the selected filters.")
    else:
        monthly = month.sort_values("month_end_date")
        left, right = st.columns((1.15, 0.85))
        fig_load = px.bar(monthly, x="month_end_date", y="avg_total_system_load", color="year", title="Average Monthly System Load", labels={"month_end_date": "Month", "avg_total_system_load": "Average system load", "year": "Year"})
        left.plotly_chart(style_fig(fig_load), use_container_width=True)
        annual = monthly.groupby("year", as_index=False).agg(total_apprehended=("total_cbp_apprehended", "sum"), total_transferred=("total_cbp_transferred_out", "sum"), total_discharged=("total_hhs_discharged", "sum"))
        annual_long = annual.melt(id_vars="year", var_name="metric", value_name="value")
        fig_flow = px.bar(annual_long, x="year", y="value", color="metric", barmode="group", title="Annual Flow Comparison", labels={"year": "Year", "value": "Count", "metric": ""}, color_discrete_map={"total_apprehended": COLORS["blue"], "total_transferred": COLORS["amber"], "total_discharged": COLORS["green"]})
        fig_flow.for_each_trace(lambda t: t.update(name={"total_apprehended": "CBP apprehended", "total_transferred": "CBP transferred out", "total_discharged": "HHS discharged"}.get(t.name, t.name)))
        right.plotly_chart(style_fig(fig_flow), use_container_width=True)

with tab_ops:
    st.subheader("Operations Monitor")
    if feed.empty:
        empty("No daily feed data matches the selected filters.")
    else:
        daily = feed.sort_values("report_date")
        rolling_window = st.slider(
            "Trend smoothing window",
            7,
            45,
            14,
            step=1,
            help="Controls the red smoothed trend line below.",
        )
        st.caption("Smaller windows react faster. Larger windows smooth short-term spikes.")
        trend = aggregate_daily(daily, frequency)
        trend = trend.dropna(subset=[primary_metric]).copy()
        trend[f"{primary_metric}_rolling"] = trend[primary_metric].rolling(rolling_window, min_periods=1).mean()
        if trend.empty:
            empty("No values exist for the selected primary metric after applying the filters.")
            st.warning("Choose a different primary metric or broaden the filters.")
        fig_primary = px.line(trend, x="report_date", y=[primary_metric, f"{primary_metric}_rolling"], title=f"{METRIC_LABELS[primary_metric]} Trend ({frequency})", labels={"report_date": "Date", "value": METRIC_LABELS[primary_metric], "variable": ""}, color_discrete_map={primary_metric: COLORS["blue"], f"{primary_metric}_rolling": COLORS["red"]})
        fig_primary.for_each_trace(lambda t: t.update(name={primary_metric: "Actual", f"{primary_metric}_rolling": f"{rolling_window}-period average"}.get(t.name, t.name)))
        st.plotly_chart(style_fig(fig_primary, 380), use_container_width=True)

        weekly = daily.set_index("report_date").resample("W").agg(total_system_load=("total_system_load", "mean"), hhs_care=("hhs_care", "mean"), cbp_custody=("cbp_custody", "mean"), cbp_apprehended=("cbp_apprehended", "sum"), cbp_transferred_out=("cbp_transferred_out", "sum"), hhs_discharged=("hhs_discharged", "sum")).reset_index()
        left, right = st.columns(2)
        fig_weekly_load = px.line(weekly, x="report_date", y=["total_system_load", "hhs_care", "cbp_custody"], title="Weekly Average Load and Custody", labels={"report_date": "Week", "value": "Average count", "variable": ""})
        fig_weekly_load.for_each_trace(lambda t: t.update(name={"total_system_load": "System load", "hhs_care": "HHS care", "cbp_custody": "CBP custody"}.get(t.name, t.name)))
        left.plotly_chart(style_fig(fig_weekly_load), use_container_width=True)
        flow_long = weekly.melt(id_vars="report_date", value_vars=["cbp_apprehended", "cbp_transferred_out", "hhs_discharged"], var_name="metric", value_name="value")
        fig_weekly_flow = px.bar(flow_long, x="report_date", y="value", color="metric", title="Weekly Intake, Transfers, and Discharges", labels={"report_date": "Week", "value": "Weekly total", "metric": ""}, color_discrete_map={"cbp_apprehended": COLORS["blue"], "cbp_transferred_out": COLORS["amber"], "hhs_discharged": COLORS["green"]})
        fig_weekly_flow.for_each_trace(lambda t: t.update(name={"cbp_apprehended": "CBP apprehended", "cbp_transferred_out": "CBP transferred out", "hhs_discharged": "HHS discharged"}.get(t.name, t.name)))
        right.plotly_chart(style_fig(fig_weekly_flow), use_container_width=True)

with tab_risk:
    st.subheader("Backlog & Risk")
    top_driver = max(risk_drivers, key=risk_drivers.get) if risk_drivers else "N/A"
    c1, c2, c3 = st.columns(3)
    c1.metric("Risk Score", f"{risk_score:.0f}/100", risk_label)
    c2.metric("Top Risk Driver", top_driver)
    c3.metric("Selected Daily Rows", fmt(len(feed)))
    if top_driver != "N/A":
        st.caption(f"Why this matters: {RISK_DRIVER_HELP.get(top_driver, 'This factor is contributing most to the current risk score.')}")
    if month.empty:
        empty("No monthly summary records match the selected filters.")
    else:
        monthly = month.sort_values("month_end_date").copy()
        monthly["transfer_gap"] = monthly["total_cbp_apprehended"] - monthly["total_cbp_transferred_out"]
        left, right = st.columns(2)
        fig_offset = px.line(monthly, x="month_end_date", y="avg_discharge_offset_ratio", color="year", markers=True, title="Average Discharge Offset Ratio by Month", labels={"month_end_date": "Month", "avg_discharge_offset_ratio": "Offset ratio", "year": "Year"})
        fig_offset.add_hline(y=1, line_dash="dash", line_color=COLORS["red"], annotation_text="Break-even", annotation_position="top left")
        left.plotly_chart(style_fig(fig_offset), use_container_width=True)
        fig_gap = px.bar(monthly, x="month_end_date", y="transfer_gap", color="transfer_gap", color_continuous_scale=["#16a34a", "#f59e0b", "#ef4444"], title="Monthly Apprehension-to-Transfer Gap", labels={"month_end_date": "Month", "transfer_gap": "Apprehended minus transferred"})
        right.plotly_chart(style_fig(fig_gap), use_container_width=True)
    if not feed.empty:
        fig_backlog = px.area(feed.sort_values("report_date"), x="report_date", y="backlog_accumulation_14d", title="14-Day Backlog Accumulation", labels={"report_date": "Date", "backlog_accumulation_14d": "14-day backlog"}, color_discrete_sequence=[COLORS["red"]])
        st.plotly_chart(style_fig(fig_backlog, 330), use_container_width=True)

with tab_forecast:
    st.subheader("Forecast & Anomalies")
    if feed.empty:
        empty("No daily feed data matches the selected filters.")
    else:
        fctl1, fctl2, fctl3 = st.columns(3)
        anomaly_threshold = fctl1.slider("Anomaly sensitivity", 1.5, 4.0, 2.5, step=0.1)
        forecast_horizon = fctl2.slider("Forecast horizon days", 7, 90, 30, step=1)
        forecast_lookback = fctl3.slider("Forecast training days", 30, 365, 120, step=5)
        anomaly_window = st.slider(
            "Anomaly baseline window",
            7,
            45,
            14,
            step=1,
            help="Controls the rolling baseline used to flag anomalies.",
        )
        st.caption(
            "Forecast horizon controls how many future days are projected. "
            "Training days controls how much recent history is used to estimate the trend."
        )

        anomalies = add_anomaly_columns(feed, primary_metric, anomaly_window, anomaly_threshold)
        anomaly_points = anomalies[anomalies["is_anomaly"]].copy()
        fig_anom = px.line(anomalies, x="report_date", y=primary_metric, title=f"{METRIC_LABELS[primary_metric]} Anomaly Detection", labels={"report_date": "Date", primary_metric: METRIC_LABELS[primary_metric]}, color_discrete_sequence=[COLORS["blue"]])
        fig_anom.add_trace(go.Scatter(x=anomaly_points["report_date"], y=anomaly_points[primary_metric], mode="markers", marker=dict(color=COLORS["red"], size=10, symbol="diamond"), name="Anomaly"))
        st.plotly_chart(style_fig(fig_anom, 390), use_container_width=True)
        if anomaly_points.empty:
            st.success("No anomalies detected for the selected metric and sensitivity.")
        else:
            st.write("Recent anomalies")
            anomaly_table = (
                anomaly_points.sort_values("report_date", ascending=False)[
                    ["report_date", primary_metric, "z_score", "direction"]
                ]
                .head(15)
                .rename(columns=TABLE_ALIASES)
            )
            if "Anomaly Score" in anomaly_table.columns:
                anomaly_table["Anomaly Score"] = anomaly_table["Anomaly Score"].round(2)
            st.dataframe(anomaly_table, use_container_width=True, hide_index=True)

        history, forecast = forecast_metric(feed, primary_metric, forecast_horizon, forecast_lookback)
        if forecast.empty:
            empty("At least 8 historical records are needed to generate a forecast.")
        else:
            fig_forecast = go.Figure()
            fig_forecast.add_trace(go.Scatter(x=history["report_date"], y=history[primary_metric], mode="lines", name="History", line=dict(color=COLORS["slate"])))
            fig_forecast.add_trace(go.Scatter(x=forecast["report_date"], y=forecast["forecast"], mode="lines", name="Forecast", line=dict(color=COLORS["purple"], width=3)))
            fig_forecast.add_trace(go.Scatter(x=forecast["report_date"], y=forecast["upper"], mode="lines", name="Upper band", line=dict(width=0), showlegend=False))
            fig_forecast.add_trace(go.Scatter(x=forecast["report_date"], y=forecast["lower"], mode="lines", name="95% confidence band", fill="tonexty", fillcolor="rgba(124, 58, 237, 0.16)", line=dict(width=0)))
            fig_forecast.update_layout(title=f"{forecast_horizon}-Day Forecast: {METRIC_LABELS[primary_metric]}")
            st.plotly_chart(style_fig(fig_forecast, 390), use_container_width=True)
            f1, f2, f3 = st.columns(3)
            f1.metric("Forecast start", f"{forecast['report_date'].min():%b %d, %Y}")
            f2.metric("Forecast end", f"{forecast['report_date'].max():%b %d, %Y}")
            f3.metric(
                "Final forecast",
                fmt(forecast["forecast"].iloc[-1]),
                pct_delta(forecast["forecast"].iloc[-1], history[primary_metric].iloc[-1]),
            )
            st.caption(
                f"The current horizon projects {forecast_horizon} days beyond "
                f"{history['report_date'].max():%b %d, %Y}."
            )

with tab_scenario:
    st.subheader("Scenario Lab")
    st.markdown(
        '<div class="section-note">Use this to test: more transfers or HHS discharges should reduce pressure; more apprehensions should increase pressure. Watch the Scenario difference metric.</div>',
        unsafe_allow_html=True,
    )
    if len(kpi) < 5:
        empty("Not enough KPI data for the selected filters to run a scenario.")
    else:
        a, b, c = st.columns(3)
        transfer_change = a.slider("CBP transfers out change (%)", -30, 60, 10)
        discharge_change = b.slider("HHS discharges change (%)", -30, 60, 10)
        intake_change = c.slider("CBP apprehensions change (%)", -30, 60, 0)
        recent = kpi.sort_values("report_date").tail(30).copy()
        recent["cbp_apprehended_sim"] = recent["cbp_apprehended"] * (1 + intake_change / 100)
        recent["cbp_transferred_out_sim"] = recent["cbp_transferred_out"] * (1 + transfer_change / 100)
        recent["hhs_discharged_sim"] = recent["hhs_discharged"] * (1 + discharge_change / 100)
        recent["net_intake_pressure_sim"] = recent["cbp_apprehended_sim"] - recent["cbp_transferred_out_sim"] - recent["hhs_discharged_sim"]
        recent["system_load_sim"] = recent["total_system_load"].iloc[0] + recent["net_intake_pressure_sim"].cumsum()
        baseline_pressure = recent["net_intake_pressure"].sum()
        scenario_pressure = recent["net_intake_pressure_sim"].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Baseline 30-day pressure", fmt(baseline_pressure))
        m2.metric("Scenario 30-day pressure", fmt(scenario_pressure))
        m3.metric("Scenario difference", fmt(scenario_pressure - baseline_pressure))
        fig_sim = px.line(recent, x="report_date", y=["net_intake_pressure", "net_intake_pressure_sim"], title="Baseline vs Scenario Net Intake Pressure", labels={"report_date": "Date", "value": "Net intake pressure", "variable": ""}, color_discrete_map={"net_intake_pressure": COLORS["muted"], "net_intake_pressure_sim": COLORS["red"]})
        fig_sim.for_each_trace(lambda t: t.update(name={"net_intake_pressure": "Baseline", "net_intake_pressure_sim": "Scenario"}.get(t.name, t.name)))
        st.plotly_chart(style_fig(fig_sim, 360), use_container_width=True)
        fig_load_sim = px.line(recent, x="report_date", y="system_load_sim", title="Projected Scenario System Load", labels={"report_date": "Date", "system_load_sim": "Projected load"}, color_discrete_sequence=[COLORS["blue"]])
        st.plotly_chart(style_fig(fig_load_sim, 320), use_container_width=True)

with tab_data:
    st.subheader("Data Quality")
    c1, c2, c3 = st.columns(3)
    c1.metric("Dashboard feed rows", fmt(len(feed_all)))
    c2.metric("KPI daily rows", fmt(len(kpi_all)))
    c3.metric("Monthly summary rows", fmt(len(month_all)))
    st.dataframe(pd.DataFrame({"View": ["Dashboard Feed", "Daily KPI", "Monthly Summary"], "Selected rows": [len(feed), len(kpi), len(month)], "Start": [feed["report_date"].min(), kpi["report_date"].min(), month["month_start_date"].min()], "End": [feed["report_date"].max(), kpi["report_date"].max(), month["month_end_date"].max()]}), use_container_width=True, hide_index=True)
    st.subheader("Monthly Summary Highlights")
    if month.empty:
        empty("No monthly summary rows match the selected filters.")
    else:
        latest_month = month.sort_values("month_end_date").iloc[-1]
        b1, b2, b3, b4 = st.columns(4)
        b1.markdown(
            f'<div class="banner"><div class="banner-title">Latest Month</div><div class="banner-value">{latest_month["month_end_date"]:%b %Y}</div></div>',
            unsafe_allow_html=True,
        )
        b2.markdown(
            f'<div class="banner"><div class="banner-title">Avg System Load</div><div class="banner-value">{fmt(latest_month["avg_total_system_load"])}</div></div>',
            unsafe_allow_html=True,
        )
        b3.markdown(
            f'<div class="banner"><div class="banner-title">Net Intake Pressure</div><div class="banner-value">{fmt(latest_month["total_net_intake_pressure"])}</div></div>',
            unsafe_allow_html=True,
        )
        b4.markdown(
            f'<div class="banner"><div class="banner-title">Discharge Offset</div><div class="banner-value">{fmt(latest_month["avg_discharge_offset_ratio"], 2)}</div></div>',
            unsafe_allow_html=True,
        )

        monthly_table = month.sort_values("month_end_date", ascending=False)[
            [
                "month_end_date",
                "record_count",
                "total_cbp_apprehended",
                "total_cbp_transferred_out",
                "total_hhs_discharged",
                "avg_total_system_load",
                "total_net_intake_pressure",
                "avg_discharge_offset_ratio",
            ]
        ].head(12)
        monthly_table = monthly_table.rename(
            columns={
                "month_end_date": "Month",
                "record_count": "Records",
                "total_cbp_apprehended": "CBP Apprehended",
                "total_cbp_transferred_out": "CBP Transferred Out",
                "total_hhs_discharged": "HHS Discharged",
                "avg_total_system_load": "Avg System Load",
                "total_net_intake_pressure": "Net Intake Pressure",
                "avg_discharge_offset_ratio": "Discharge Offset Ratio",
            }
        )
        st.dataframe(monthly_table, use_container_width=True, hide_index=True)


