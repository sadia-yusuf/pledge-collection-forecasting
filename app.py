"""
Pledge-Collection Forecasting
=============================
Turns Room to Read's static "promises to give" aging schedule (FY2025 Note D)
into a rolling, assumption-driven cash forecast.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py

Deploy:
    Push this repo to GitHub, then point Streamlit Community Cloud
    (share.streamlit.io) at app.py. No other setup required.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# 1. SOURCE DATA
#    Every figure below is transcribed from Room to Read's FY2025 audited
#    consolidated financial statements, Note D (Promises to Give).
#    Nothing here is estimated except the realisation rates, which are
#    clearly separated out as user-adjustable assumptions below.
# ---------------------------------------------------------------------------

AGING_BANDS_M = {
    "< 1 year": 22.81,
    "1 – 5 years": 19.29,
    "> 5 years": 2.00,
}
DISCOUNT_M = -4.59                 # present-value discount on the >1yr bands
FACE_VALUE_NET_M = 39.52           # = sum(AGING_BANDS_M) + DISCOUNT_M
FY25_OPERATING_CASH_M = 0.32       # actual FY2025 net cash from operating activities
FY25_CHANGE_IN_NET_ASSETS_M = 12.49  # the reported accounting "surplus" for scale

DEFAULT_RATES = {"< 1 year": 90, "1 – 5 years": 65, "> 5 years": 40}


# ---------------------------------------------------------------------------
# 2. CORE CALCULATION
#    This is the whole model: face value x realisation rate = expected cash.
#    Kept as small, pure functions so the logic is easy to unit-test and
#    easy to swap out once real donor-cohort collection history is available.
# ---------------------------------------------------------------------------

def risk_adjust(face_value_m: float, realisation_rate_pct: float) -> float:
    """Apply a realisation-rate assumption to a face-value pledge balance."""
    return face_value_m * realisation_rate_pct / 100


def build_band_table(rates: dict) -> pd.DataFrame:
    """One row per aging band: face value, assumed rate, expected cash."""
    rows = []
    for band, face_value in AGING_BANDS_M.items():
        rows.append({
            "Aging band": band,
            "Face value ($M)": face_value,
            "Realisation rate": rates[band],
            "Expected cash ($M)": round(risk_adjust(face_value, rates[band]), 2),
        })
    return pd.DataFrame(rows)


def build_annual_forecast(band_table: pd.DataFrame) -> pd.DataFrame:
    """
    Spread each band's expected cash across an annual collection horizon.
    Assumption: the <1yr band collects entirely in Year 1; the 1-5yr band
    collects evenly across Years 2-5; the >5yr band is shown as a single
    terminal "5+ years" bucket. This mirrors how the aging bands themselves
    are defined in Note D.
    """
    expected = dict(zip(band_table["Aging band"], band_table["Expected cash ($M)"]))
    year1 = expected["< 1 year"]
    yr2_to_5_each = expected["1 – 5 years"] / 4
    beyond = expected["> 5 years"]

    return pd.DataFrame({
        "Period": ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5", "5+ years"],
        "Expected cash ($M)": [year1, yr2_to_5_each, yr2_to_5_each, yr2_to_5_each,
                                yr2_to_5_each, beyond],
    })


# ---------------------------------------------------------------------------
# 3. STREAMLIT UI
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Pledge-Collection Forecasting", page_icon="📊", layout="wide")

st.sidebar.header("Realisation rate assumptions")
st.sidebar.caption(
    "Illustrative defaults — replace with real donor-cohort collection "
    "and write-off history once available."
)
rates = {
    band: st.sidebar.slider(band, 0, 100, default, step=1, format="%d%%")
    for band, default in DEFAULT_RATES.items()
}

band_table = build_band_table(rates)
forecast = build_annual_forecast(band_table)
total_adjusted_m = band_table["Expected cash ($M)"].sum()
next_12mo_m = band_table.loc[band_table["Aging band"] == "< 1 year", "Expected cash ($M)"].iloc[0]

st.title("📊 Pledge-Collection Forecasting")
st.markdown(
    "Room to Read's **$39.5M promises-to-give** balance is disclosed once a year as a "
    "static aging schedule (Note D). This tool turns that schedule into a rolling cash "
    "forecast — adjust the realisation rate for each band in the sidebar and watch the "
    "forecast move."
)

col1, col2, col3 = st.columns(3)
col1.metric(
    "Risk-adjusted pledge value",
    f"${total_adjusted_m:.1f}M",
    f"{total_adjusted_m / FACE_VALUE_NET_M * 100:.0f}% of face value",
)
col2.metric("Expected in next 12 months", f"${next_12mo_m:.1f}M")
col3.metric(
    "FY2025 actual operating cash",
    f"${FY25_OPERATING_CASH_M:.2f}M",
    help="For scale: the $12.49M reported surplus converted to only this much real cash.",
)

st.divider()
st.subheader("Aging bands and assumptions")
st.dataframe(
    band_table.style.format({"Face value ($M)": "{:.2f}", "Realisation rate": "{:.0f}%"}),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Annual cash-in forecast")
fig = go.Figure(data=[go.Bar(
    x=forecast["Period"],
    y=forecast["Expected cash ($M)"],
    text=[f"${v:.1f}M" for v in forecast["Expected cash ($M)"]],
    textposition="outside",
    marker_color=["#0B4A6F", "#2A7F9E", "#2A7F9E", "#2A7F9E", "#2A7F9E", "#8FC1D4"],
)])
fig.update_layout(
    yaxis_title="Expected cash ($M)",
    showlegend=False,
    height=380,
    margin=dict(t=10, b=10, l=10, r=10),
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("From prototype to production"):
    st.markdown(
        "- **Today:** illustrative rates, built to show the mechanism.\n"
        "- **Next:** replace the sliders with real donor-cohort collection and "
        "write-off history pulled from the pledge subledger.\n"
        "- **Then:** automate the aging refresh monthly and feed this into a "
        "13-week cash forecast so treasury sees both horizons together."
    )

st.caption(
    "Aging bands and face value from Room to Read's FY2025 audited Note D "
    "(Promises to Give). Realisation-rate assumptions are illustrative and "
    "adjustable — not disclosed donor data."
)
