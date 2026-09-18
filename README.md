# Pledge-Collection Forecasting

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

## What it does

- Reads the real FY2025 aging bands and face value from Note D
- Lets you set a realisation rate per band with a slider
- Computes a risk-adjusted expected-cash figure, live
- Spreads that into an annual forecast (Year 1 → 5+ years)
- Compares the risk-adjusted forecast against face value and against actual
  FY2025 operating cash, for scale

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```


## Data source and limitations

Aging bands and face value are transcribed from Room to Read's FY2025 audited
consolidated financial statements, Note D (Promises to Give). Realisation-rate
assumptions are **illustrative and adjustable** — real donor-cohort collection
and write-off history isn't publicly disclosed, so the defaults are a
reasonable starting point, not a claim about actual collectability.

## Next steps for a production version

- Replace the sliders with real historical realisation rates by donor cohort
- Pull the aging table directly from the general ledger / pledge subledger
  instead of a hardcoded snapshot
- Feed the output into a 13-week cash forecast alongside other cash sources
