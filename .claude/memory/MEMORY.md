# Market Week — Workflow Memory

> **SYNC NOTE:** This file exists in two places. When updating either, always write to both:
> - Repo (version-controlled): `.claude/memory/MEMORY.md`
> - Global (Claude reads this): `~/.claude/projects/C--Users-Akhil-Documents-cc4e-course-market-week/memory/MEMORY.md`

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

## System Overview Diagram

- **File:** `weekly-newsletter/output/system-overview.html`
- **Last updated:** 2026-03-13
- Open in browser and Ctrl+P → Save as PDF to share
- **Update this file when:** a new content type is added, a new distribution channel goes live, a major integration changes (e.g. Substack automated, LinkedIn API), or new data sources are added
- When updating, also bump the "Generated" date in the footer

## Publishing Standards

- Subscriber emails must include the **Framework Foundry banner**
- Substack posts must be delivered as **HTML** (not Markdown) — save to `output/` as `.html` and paste into Substack editor

## Market IQ Flashcards

### ACTIVE: Link economic indicator mentions to flashcards in every edition
Every mention of a tracked economic indicator in the newsletter HTML **must** be
hyperlinked to its flashcard entry. This applies to all future editions now.

Term → anchor mapping:
- "CPI" / "consumer price index" → `/market-iq#cpi`
- "NFP" / "non-farm payrolls" → `/market-iq#nfp`
- "yield curve" → `/market-iq#yield-curve`
- "Fed funds rate" / "FFR" / "federal funds rate" → `/market-iq#ffr`
- "PCE" / "personal consumption expenditures" → `/market-iq#pce`

Implementation notes:
- Add `id` anchors to each flashcard block when building the live page
- In `build_site.py` / `build_combined_site.py`, add a post-render pass that
  regex-replaces known indicator terms in the newsletter body with `<a>` tags
- Maintain a term→anchor mapping dict (abbreviations + full names + press shorthand)
- Links open the Market IQ page scrolled to the right card (anchor link, same-site)

### Go-live: use auto-pull for card data
When integrating Market IQ flashcards into the live site, card data must be
populated from the existing pipeline (`fetch_data.py` / FRED / yfinance fixtures)
— **not** hardcoded. The current `output/market-iq-flashcards_mockup.html` has
hardcoded values for review only.

Update cadences per card:
- CPI → monthly (~2nd Tuesday, BLS)
- FFR → 8× / year (FOMC decision days)
- NFP → monthly (1st Friday, BLS)
- PCE → monthly (~last Friday, BEA)
- Yield Curve → monthly snapshot (10Y & 2Y already in fixtures)

## Workflow Preferences

### End-of-session GitHub commit
When a session's work looks complete and content looks good, always ask:
"Ready to commit the code changes to GitHub?"
before committing source code. The `publish_daybreak.sh` script auto-commits
generated content (fixtures, site), but source code changes should be committed
separately with explicit user sign-off.

---

### Price verification (--verify flag)
`generate_newsletter.py --live --verify` cross-checks yfinance prices against
FRED (Gold, 10Y Treasury) and Stooq (equities, USD Index) before generating.
Raises `PriceDiscrepancyError` if any asset diverges >2%. Requires `pandas_datareader`.
