# Market Week — Workflow Memory

## Fixture Data Workflow

### REQUIRED: Verify all prices against 2 independent sources before writing any fixture file

When creating or updating any `fixtures/*.json` file with market prices:

1. **Look up each asset from at least 2 independent sources** (e.g., FRED, Yahoo Finance, CNBC, Investing.com, MarketWatch, Nasdaq.com, US Treasury H.15, pricegold.net).
2. **Cross-reference closing prices** — note any discrepancies between sources and flag them.
3. **Only use confirmed closes** — mark intraday open/high/low as "estimated" if not independently verified.
4. **Do not fabricate or extrapolate prices** — a plausible-looking number is not a correct number.

**Why this matters:** In the Feb 21 fixture, fabricated equity values were ~10% off (S&P 500: 6,205 vs actual 6,910; Dow: 45,312 vs actual 49,626; USD Index: 107.85 vs actual 97.80). Only gold was close because it was specifically researched.

### Confidence levels to record per asset
- **High**: closing price confirmed by 2+ primary sources (FRED, official exchange data)
- **Medium**: closing price confirmed by 1 primary source; mid-week values interpolated
- **Estimated**: open/high/low inferred from context when intraday data unavailable

---

## Architecture Notes

### generate_price_chart(prefix=)
`data/chart.py` accepts a `prefix` param (default `"chart"`). Always pass
`prefix="intl_chart"` when calling from `generate_intl_newsletter.py` to
avoid clobbering the US chart for the same date.

### generate_pdf(filename=)
`data/pdf_export.py` accepts a `filename` param (default `newsletter_{date}.pdf`).
Always pass `filename=f"intl_newsletter_{date_str}.pdf"` from the intl generator
to avoid clobbering the US PDF for the same date.

### Newsletter generation order
Running both generators for the same date is safe **only if** the above params
are used. The intl generator used to rename outputs, deleting the US files.

### Site rebuild workflow
1. Run `generate_newsletter.py --date YYYY-MM-DD --pdf`
2. Run `generate_intl_newsletter.py --date YYYY-MM-DD --pdf` (if intl edition needed)
3. Run `build_combined_site.py`
4. Commit: `site/`, updated `output/` files
5. Push

### Stale fixture warning
`fetch_data.py` prints a WARNING if the closest fixture is >2 days from the
requested date. This means data is stale — use `--live` or create a new fixture.

### Price verification (--verify flag)
`generate_newsletter.py --live --verify` cross-checks yfinance prices against
FRED (Gold, 10Y Treasury) and Stooq (equities, USD Index) before generating.
Raises `PriceDiscrepancyError` if any asset diverges >2%. Requires `pandas_datareader`.
