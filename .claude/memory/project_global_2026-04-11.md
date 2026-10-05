---
name: Global Investor Edition 2026-04-11 session
description: What was done and what remains for the April 11 global edition
type: project
originSessionId: c0f055ba-89fc-4342-b061-32b252e61b13
---
## Status: Web published. Substack and social posts still pending.

**Why:** Weekly global edition run for week ending Fri Apr 10, 2026.

---

## What was done

### Data
- Ran 4 Perplexity queries + 3 follow-up verification queries
- Perplexity had major errors: S&P reported as 6,034 (actual 6,816.89), DXY as 105.23 (actual 98.70), JPY/USD as 0.01 (actual 0.006282), Nasdaq weekly as +4.1% (actual +0.3%), Dow weekly as +3.2% (actual -0.6%)
- User supplied correct Friday Apr 10 closes; weekly moves confirmed as Thu Apr 9 → Fri Apr 10 delta
- Fixtures built with `build_global_perplexity_fixtures.py --overwrite`

### Key verified closes (Apr 10, 2026)
- S&P 500: 6,816.89 (+0.5% wk) | Dow: 47,916.57 (-0.6% wk) | Nasdaq: 22,902.89 (+0.3% wk)
- Russell 2000: 2,630.59 (+0.4%) | DXY: 98.70 (-0.5%) | VIX: 15.67 (-12.5%)
- DAX: 23,803.95 (+2.74%) | FTSE: 10,600.53 (+1.57%) | CAC 40: 8,259.60 (+3.73%)
- WTI: 100.46 (-10.3% wk) | Gold: 4,771 (+2.0%) | Nat Gas: 3.04 (+5.59%)
- 10Y: 4.32% (+4 bps) | 30Y: 4.91% (+1 bps) | JPY/USD: 0.006282 (+0.32%)
- EUR/USD: 1.1711 | GBP/USD: 1.3423 | AUD/USD: 0.69 (+1.21%) | CHF/USD: 1.25

### Newsletter
- Generated, then fully rewritten to match April 4 style: bold/opinionated, cause-and-effect, One Trade section (FEZ long), no wrapper headers ("Page 1" etc removed), no Week Range in tables, fixed income merged into commodity table
- Em dashes replaced with " - " throughout (new persistent rule saved to memory)
- Title chosen: "Crude Breaks, Europe Leads - A Global Regime Shift in Motion"
- File: `weekly-newsletter/output/global_newsletter_2026-04-11.md`

### Published
- Site built via `build_combined_site.py`
- Committed and pushed to master → live at frameworkfoundry.info/global/2026-04-11/
- Commit: 79f28d6

---

## Still pending (this session)
1. **Substack HTML version** - not yet drafted
2. **Social media posts** - X thread, LinkedIn, Substack note (after Substack approved)

**How to apply:** When resuming, skip straight to Substack draft using the approved MD file as source. Do not regenerate.
