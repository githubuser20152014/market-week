---
name: market-iq-flashcards-indicator-linking-and-data-sourcing
description: "Term-to-anchor hyperlink mapping for economic indicators, and the rule that card data must be pulled live, not hardcoded"
metadata: 
  node_type: memory
  type: project
  originSessionId: e03b998a-3cab-497f-abac-389a5dd8f548
  modified: 2026-07-25T11:38:01.796Z
---

### ACTIVE: link economic indicator mentions to flashcards in every edition
Every mention of a tracked economic indicator in the newsletter HTML must be
hyperlinked to its flashcard entry, in all future editions.

Term → anchor mapping:
- "CPI" / "consumer price index" → `/market-iq#cpi`
- "NFP" / "non-farm payrolls" → `/market-iq#nfp`
- "yield curve" → `/market-iq#yield-curve`
- "Fed funds rate" / "FFR" / "federal funds rate" → `/market-iq#ffr`
- "PCE" / "personal consumption expenditures" → `/market-iq#pce`

Implementation: add `id` anchors to each flashcard block (e.g. `id="cpi"`);
in `build_site.py` / `build_combined_site.py`, add a post-render regex pass
that replaces known indicator terms in the newsletter body with `<a>` tags
using a term→anchor mapping dict (abbreviations + full names + press
shorthand). Links open the Market IQ page pre-scrolled to the card (anchor
link, same-site, no new tab).

### Go-live: use auto-pull for card data
Card data must be populated from the existing pipeline (`fetch_data.py` /
FRED / yfinance fixtures), not hardcoded. `output/market-iq-flashcards_mockup.html`
has hardcoded values for review only.

Update cadences: CPI monthly (~2nd Tue, BLS); FFR 8×/yr (FOMC days); NFP
monthly (1st Fri, BLS); PCE monthly (~last Fri, BEA); Yield Curve monthly
snapshot (10Y & 2Y already in fixtures).
