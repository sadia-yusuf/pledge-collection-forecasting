# Pledge-Collection Forecasting

**🔗 [Open the live app](https://pledge-collection-forecasting-m24pncxb5n93zgunwvdn3s.streamlit.app/)**

An interactive Streamlit tool that turns a static pledge-aging schedule into a
rolling, assumption-driven cash forecast — built against Room to Read's FY2025
audited consolidated financial statements.

## Why this exists

Nonprofit "promises to give" (pledges) are usually disclosed once a year as a
static aging table: how much is due in under a year, 1–5 years, and beyond 5
years. That table alone doesn't tell you when the cash actually arrives.

This tool applies a realisation-rate assumption to each aging band and
produces a rolling forecast of expected cash inflows — the same mechanic that
explains why Room to Read's reported FY2025 change in net assets ($12.49M)
converted to only $0.32M of real operating cash. Most of the "surplus" was
pledges recognised as revenue before the cash was collected.

## Pages

**Home (`app.py`) — Pledge-Collection Forecasting**
- Reads the real FY2025 aging bands and face value from Note D
- Lets you set a realisation rate per band with a slider
- Computes a risk-adjusted expected-cash figure, live
- Spreads that into an annual forecast (Year 1 → 5+ years)
- Compares the risk-adjusted forecast against face value and against actual
  FY2025 operating cash, for scale

**13-Week Cash Forecast (`pages/1_13_Week_Cash_Forecast.py`)**
- Rolls a starting cash balance forward week by week: `ending = beginning +
  inflows − outflows`, with each week's ending balance becoming the next
  week's opening balance
- Pledge collections feed from the same <1yr band and realisation rate as
  the Home page, just at weekly instead of annual resolution
- Seasonality toggles (Q1 pledge season, a gala-week inflow spike) are
  grounded in Note P's own disclosure of seasonal cash concentration
- Flags any week where the projected balance falls below a minimum safe
  buffer — the week-level risk an annual liquidity view can't see

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will automatically pick up both pages and show them in the sidebar.

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, point it at this repo, branch `main`, main file path `app.py`.
4. Deploy — you get a public URL in a couple of minutes, with both pages live.

## Data source and limitations

Aging bands, face value, ending cash, and total operating expense are
transcribed from Room to Read's FY2025 audited consolidated financial
statements (Note D and the primary statements). Realisation-rate,
seasonality, outflow run-rate, and buffer assumptions are **illustrative
and adjustable** — real donor-cohort collection history and the actual
AP/payroll calendar aren't publicly disclosed, so the defaults are a
reasonable starting point, not a claim about actual results.

## Next steps for a production version

- Replace the realisation-rate and seasonality sliders with real historical
  data by donor cohort and by week
- Pull both the pledge aging table and the weekly outflow calendar directly
  from the general ledger / subledgers instead of hardcoded snapshots
- Add a donor-restriction release tracker (time-restricted vs purpose-
  restricted funds) alongside the two cash views already here

## License

MIT — see [LICENSE](LICENSE).
