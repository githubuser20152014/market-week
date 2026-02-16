# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Weekly Economic Newsletter Generator** — A Python CLI tool (`generate_newsletter.py`) that auto-generates a Markdown newsletter for active ETF investors. Runs weekly to review the past 7 days' macro events, major indices performance, and upcoming events with positioning tips. Output: `newsletter_[YYYY-MM-DD].md`. US-focused initially; designed for easy international expansion (Nikkei, FTSE, ECB).

Target user: Diversified ETF holder tilting on macro regimes (e.g., defensives on volatility).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run newsletter generation (defaults to today)
python generate_newsletter.py

# Run for a specific date
python generate_newsletter.py --date 2026-02-16

# Preview to stdout without saving
python generate_newsletter.py --preview
```

## Architecture

```
weekly-newsletter/
├── generate_newsletter.py   # Main CLI entry point: fetch → process → render → save
├── data/
│   ├── fetch_data.py        # API calls to Alpha Vantage & Finnhub → JSON
│   └── process_data.py      # Compute % changes, filter/group events, generate tips
├── templates/
│   └── newsletter_template.md  # Jinja2 Markdown template
├── config/
│   ├── indices.json         # Index symbol mapping (e.g., {"SPX": "^GSPC"})
│   └── api_keys.env         # Environment variable template (not committed)
├── output/                  # Generated newsletters land here
└── requirements.txt         # pandas, requests, python-dotenv, jinja2, yfinance
```

**Data flow:** `generate_newsletter.py` orchestrates: `fetch_data.py` pulls from APIs → `process_data.py` transforms raw data into structured content → Jinja2 renders the template → output saved as Markdown.

## Data Sources (Free APIs)

- **Indices**: Alpha Vantage `TIME_SERIES_DAILY` for ^GSPC, ^DJI, ^IXIC, ^RUT. Weekly % = `(close_today - close_7d_ago) / close_7d_ago`. Env var: `ALPHAVANTAGE_API_KEY`.
- **Economic Calendar**: Finnhub `/calendar/economic` with date range, filter importance > 2, keywords: CPI, GDP, Fed, ECB. Env var: `FINNHUB_API_KEY`.
- **News/Sentiment**: Finnhub `/news?category=general` filtered by keywords; RSS fallback.
- **Edge cases**: Mock JSON fixtures if APIs fail. Use latest trading day for weekends.

## Branding

Newsletter header: **"Framework Capital Weekly"**. Professional Markdown with tables.

## Expansion Points

- International indices: add to `config/indices.json` (^N225, ^FTSE) and `config/intl.json` for ECB RSS
- Email delivery: smtplib
- PDF export: weasyprint
- Automation: GitHub Actions cron
