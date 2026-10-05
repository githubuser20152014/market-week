---
name: Daybreak — What is and isn't fetched on each daily run
description: Defines the exact data fetch scope for the automated 5:15 AM Daybreak run; two things are explicitly excluded
type: feedback
---

The daily automated run (and any manual generate step) fetches ONLY:
- US equity closes (yfinance)
- International overnight indices (yfinance)
- FX rates (yfinance)
- Pre-market futures (yfinance)
- Market news headlines (RSS/Finnhub)

**Explicitly excluded — do not add these back:**

1. **Economic events calendar** — removed from `fetch_daybreak_data.py` (returns empty `{"yesterday": [], "today": []}`). Too slow, buggy, and not relevant to daily readers.

2. **Market IQ card live data** — Market IQ flashcard values (CPI, FFR, NFP, PCE, yield curve) are not fetched on the daily run. They update on their own cadence (monthly/FOMC) and are populated separately, not as part of Daybreak generation.

**Why:** Keep the automated run fast and focused. Both of these were either slow/buggy or update too infrequently to justify a daily fetch.

**How to apply:** If asked to add data sources to the Daybreak generator, check this list first. Do not propose fetching economic calendar events or Market IQ card data as part of the daily run.
