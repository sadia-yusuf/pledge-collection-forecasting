"""
13-Week Rolling Cash Forecast
==============================
A short-horizon, seasonality-aware cash forecast that complements the
annual pledge-collection model on the Home page. Where that page answers
"are we solvent this year", this page answers "can we cover payroll and
program disbursements in a specific week over the next quarter."

Grounded in Room to Read's own disclosures:
- FY2025 ending cash: $17.64M (balance sheet)
- FY2025 total operating expense: $64.57M (functional expense statement)
- Note P explicitly discloses seasonal concentration: heavy Q1 pledge
  payments, inflow spikes around gala events, large year-end gifts.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="13-Week Cash Forecast", page_icon="📅", layout="wide")

# ---------------------------------------------------------------------------
# 1. GROUNDING DATA — same source family as the Home page (app.py)
# ---------------------------------------------------------------------------
FY25_ENDING_CASH_M = 17.64
FY25_TOTAL_OPEX_M = 64.57
PLEDGE_LT1YR_FACE_M = 22.81          # Note D, <1 year band
DEFAULT_LT1YR_RATE_PCT = 90          # matches the Home page default

WEEKLY_BASELINE_OUTFLOW_M = FY25_TOTAL_OPEX_M / 52
WEEKLY_BASELINE_PLEDGE_M = (PLEDGE_LT1YR_FACE_M * DEFAULT_LT1YR_RATE_PCT / 100) / 52


# ---------------------------------------------------------------------------
# 2. CORE CALCULATION
#    Same "small pure functions" discipline as the Home page's risk_adjust()
#    and build_annual_forecast() — logic kept separate from the UI below.
# ---------------------------------------------------------------------------

def seasonality_curve(weeks: int, boost_weeks: list, boost_multiplier: float) -> np.ndarray:
    """
    Per-week multiplier on baseline pledge collections. boost_weeks are
    1-indexed week numbers that receive the multiplier (e.g. a Q1 pledge
    surge, or the weeks around a gala) — grounded in Note P's disclosure
    of seasonal cash-flow concentration.
    """
    curve = np.ones(weeks)
    for w in boost_weeks:
        if 1 <= w <= weeks:
            curve[w - 1] = boost_multiplier
    return curve


def build_forecast(starting_cash_m: float, weeks: int, outflow_adj_pct: float,
                    other_inflow_m: float, season_curve: np.ndarray) -> pd.DataFrame:
    """
    Rolls beginning cash forward week by week:
        ending[t] = beginning[t] + inflows[t] - outflows[t]
    and week t's ending balance becomes week t+1's beginning balance —
    the "roll-forward" mechanic itself.
    """
    rows = []
    beginning = starting_cash_m
    for w in range(1, weeks + 1):
        pledge_in = WEEKLY_BASELINE_PLEDGE_M * season_curve[w - 1]
        total_in = pledge_in + other_inflow_m
        total_out = WEEKLY_BASELINE_OUTFLOW_M * outflow_adj_pct / 100
        ending = beginning + total_in - total_out
        rows.append({
            "Week": w,
            "Beginning cash ($M)": round(beginning, 2),
            "Pledge collections ($M)": round(pledge_in, 2),
            "Other inflows ($M)": round(other_inflow_m, 2),
            "Outflows ($M)": round(total_out, 2),
            "Ending cash ($M)": round(ending, 2),
        })
        beginning = ending
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 3. UI
# ---------------------------------------------------------------------------

st.title("📅 13-Week Rolling Cash Forecast")
st.markdown(
    "The annual liquidity view says Room to Read has roughly 12 months of cash "
    "coverage. It can't tell you whether one specific week is tight. This forecast "
    "rolls beginning cash forward week by week — `ending = beginning + inflows − "
    "outflows` — and each week's ending balance becomes next week's opening balance."
)

st.sidebar.header("Assumptions")
starting_cash = st.sidebar.number_input(
    "Starting cash ($M)", min_value=0.0, value=FY25_ENDING_CASH_M, step=0.5,
    help="Defaults to the FY2025 audited ending cash balance.",
)
outflow_adj = st.sidebar.slider(
    "Weekly outflow run-rate (% of baseline)", 60, 140, 100, step=5,
    help=f"Baseline = FY2025 total operating expense ÷ 52 = ${WEEKLY_BASELINE_OUTFLOW_M:.2f}M/week.",
)
other_inflow = st.sidebar.slider(
    "Other weekly inflows ($M)", 0.0, 1.5, 0.85, step=0.05,
    help=("New gifts, investment distributions, etc. — outside modelled pledge "
          "collections. Default is calibrated so the full 13 weeks average out "
          "near breakeven, consistent with FY2025's actual $0.32M operating cash."),
)
q1_toggle = st.sidebar.checkbox(
    "This window includes Q1 (pledge-payment season)", value=True,
    help="Note P discloses that contributions concentrate in Q1 due to pledge payments.",
)
gala_week = st.sidebar.slider(
    "Gala week (inflow spike)", 1, 13, 8,
    help="Note P discloses inflow spikes around gala events.",
)
min_buffer = st.sidebar.number_input("Minimum safe cash buffer ($M)", value=2.0, step=0.5)

boost_weeks = list(range(1, 5)) if q1_toggle else []
boost_weeks.append(gala_week)
season = seasonality_curve(13, boost_weeks, boost_multiplier=3.0)

forecast = build_forecast(starting_cash, 13, outflow_adj, other_inflow, season)

lowest_row = forecast.loc[forecast["Ending cash ($M)"].idxmin()]
below_buffer = forecast[forecast["Ending cash ($M)"] < min_buffer]

col1, col2, col3 = st.columns(3)
col1.metric("Lowest projected balance", f"${lowest_row['Ending cash ($M)']:.1f}M",
            f"Week {int(lowest_row['Week'])}")
col2.metric("Weeks below buffer", f"{len(below_buffer)} of 13")
col3.metric("Ending balance, week 13", f"${forecast.iloc[-1]['Ending cash ($M)']:.1f}M")

if len(below_buffer) > 0:
    weeks_list = ", ".join(str(int(w)) for w in below_buffer["Week"])
    st.warning(
        f"⚠️ Projected cash dips below the ${min_buffer:.1f}M buffer in "
        f"week(s) {weeks_list}. This is the kind of week-level gap the annual "
        f"liquidity view can't see."
    )
else:
    st.success(f"Cash stays above the ${min_buffer:.1f}M buffer in every week of this forecast.")

st.subheader("Weekly cash roll-forward")
st.dataframe(forecast, use_container_width=True, hide_index=True)

st.subheader("13-week trajectory")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=forecast["Week"], y=forecast["Ending cash ($M)"],
    mode="lines+markers", name="Ending cash",
    line=dict(color="#0B4A6F", width=3),
))
fig.add_hline(y=min_buffer, line_dash="dash", line_color="#B4472E",
              annotation_text="Minimum buffer", annotation_position="bottom right")
fig.update_layout(xaxis_title="Week", yaxis_title="Cash ($M)", height=380,
                   margin=dict(t=10, b=10, l=10, r=10))
st.plotly_chart(fig, use_container_width=True)

with st.expander("How this connects to the pledge-collection model"):
    st.markdown(
        "- Pledge collections here use the **same <1yr band and realisation rate** "
        "as the Home page, just divided into weekly instead of annual buckets.\n"
        "- The Q1 and gala seasonality toggles are grounded in Room to Read's own "
        "Note P disclosure of seasonal cash-flow concentration.\n"
        "- In production, the weekly outflow baseline would come from the actual "
        "AP and payroll calendar instead of a flat run-rate."
    )

st.caption(
    "Starting cash and total operating expense are from Room to Read's FY2025 "
    "audited statements. Seasonality, outflow run-rate, and buffer assumptions "
    "are illustrative and adjustable."
)
