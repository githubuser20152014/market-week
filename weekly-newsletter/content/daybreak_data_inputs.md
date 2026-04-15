# Daybreak — Daily Data Inputs

Everything needed before writing the Morning Brief, grouped by category.

| # | Asset | Timing | Notes |
|---|-------|--------|-------|
| **US Equities - Previous Day's Close** | | | |
| 1 | S&P 500 | 4 PM ET close | Official close, not pre-market |
| 2 | Dow Jones | 4 PM ET close | |
| 3 | Nasdaq Composite | 4 PM ET close | |
| 4 | Russell 2000 | 4 PM ET close | |
| **Commodities - Current Price** | | | |
| 5 | Gold spot | Pre-market / morning | Trades 24/7 |
| 6 | WTI Crude Oil | Pre-market / morning | Trades 24/7 |
| **Bonds & Dollar** | | | |
| 7 | 10-year Treasury yield | Previous day close | As a % e.g. 4.24 |
| 8 | USD Index (DXY) | Previous day close | |
| **Pre-Market Futures** | | | |
| 9 | S&P 500 futures (ES) | Current pre-market | |
| 10 | Nasdaq 100 futures (NQ) | Current pre-market | |
| 11 | Dow futures (YM) | Current pre-market | |
| 12 | Gold futures (GC) | Current pre-market | |
| 13 | WTI Crude futures (CL) | Current pre-market | |
| **International Indices - Overnight Closes** | | | |
| 14 | Nikkei 225 | Asia close | Note if holiday |
| 15 | Hang Seng | Asia close | |
| 16 | KOSPI | Asia close | |
| 17 | Nifty 50 | Asia close | |
| 18 | ASX 200 | Asia close | |
| 19 | DAX | European close | |
| 20 | FTSE 100 | European close | |
| 21 | CAC 40 | European close | |
| 22 | Euro Stoxx 50 | European close | |
| **FX Rates** | | | |
| 23 | EUR/USD | 5 PM ET | |
| 24 | GBP/USD | 5 PM ET | |
| 25 | USD/JPY | 5 PM ET | |
| 26 | AUD/USD | 5 PM ET | |
| 27 | USD/CNH | 5 PM ET | |
| 28 | CHF/USD | 5 PM ET | |

## Timing Notes

- **Items 1-4, 7-8** - Perplexity usually gets these right after 4 PM ET
- **Items 9-13** - Best pulled the next morning pre-market (6-9 AM ET window)
- **Items 14-22** - Available by ~6 AM ET (Asia already closed, Europe closing)
- **Items 23-28** - Available after 5 PM ET or current morning rates

The sweet spot for running the brief is **7-8 AM ET** - Asia is closed, Europe is mid-session, US futures are active, and yesterday's US closes are confirmed.
