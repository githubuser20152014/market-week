---
name: Global Investor Edition 2026-03-27 — Complete
description: Published 2026-03-28. Website live. Email and Substack pending.
type: project
---

## Status
Published to GitHub Pages on 2026-03-28.

**Why:** Weekly global edition covering week ending March 27, 2026.

**How to apply:** Email and Substack still pending — do not re-publish the website.

## What was done
- Fixtures built (corrected prices: gold=4524.30, nasdaq=20948.36, wti_crude=99.64)
- Newsletter markdown edited and approved
- Economic calendar fetched via Perplexity (FRED/Finnhub unavailable)
- Site built and pushed to GitHub Pages
- build_combined_site.py daybreak_ctxs KeyError bug fixed and committed

## Pending
- Subscriber email: `cd weekly-newsletter && python send_email.py --edition global --date 2026-03-27`
- Substack post: HTML format (per memory)
