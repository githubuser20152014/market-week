---
name: fixture-data-verification-workflow
description: "Cross-source price verification required before writing any fixture file, with confidence-level tagging"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e03b998a-3cab-497f-abac-389a5dd8f548
  modified: 2026-07-25T11:38:45.873Z
---

**REQUIRED: verify all prices against 2 independent sources before writing
any `fixtures/*.json` file with market prices.**

1. Look up each asset from at least 2 independent sources (FRED, Yahoo
   Finance, CNBC, Investing.com, MarketWatch, Nasdaq.com, US Treasury H.15,
   pricegold.net).
2. Cross-reference closing prices, flag any discrepancies between sources.
3. Only use confirmed closes; mark intraday open/high/low as "estimated" if
   not independently verified.
4. Do not fabricate or extrapolate prices — a plausible-looking number is
   not a correct number.

**Why:** in the Feb 21 fixture, fabricated equity values were ~10% off
(S&P 500: 6,205 vs actual 6,910; Dow: 45,312 vs actual 49,626; USD Index:
107.85 vs actual 97.80). Only gold was close because it was specifically
researched.

**Confidence levels per asset:** High = confirmed by 2+ primary sources
(FRED, official exchange data). Medium = confirmed by 1 primary source,
mid-week values interpolated. Estimated = open/high/low inferred from
context when intraday data unavailable.
