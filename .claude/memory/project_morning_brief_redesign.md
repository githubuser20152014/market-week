---
name: Morning Brief redesign — session 2026-03-25
description: Major pipeline changes made on March 25 — bold callouts, two-section split, The One Trade, Claude-written email subject, social post wiring
type: project
---

## What was built (2026-03-25)

### Bold callouts in The Brief
Added bold formatting instruction to `_DAYBREAK_SYSTEM_PROMPT` in `data/daybreak_process_data.py`.
Targets: price figures at inflection points, cross-asset tension phrases, named risks/catalysts.
Aim: 6–10 bold phrases per edition.

### Section split: The Brief → two sections
`plain_summary` (4 paragraphs) now splits at paragraph index 2:
- **The Brief** — narrative + paras [0-1]: what happened + why
- **What it means for you** — paras [2-3]: investor implications + going into today

Returns `(narrative, brief_body, investor_section, one_trade, email_subject, tips)` from `build_daybreak_narrative_sections()`.
Template: `weekly-newsletter/templates/daybreak_template.md`
HTML: `weekly-newsletter/daybreak_build_site.py`

### The One Trade
New 5th JSON key from Claude API: `{ticker, direction, thesis, confirm, risk}`.
- Claude picks the single highest-conviction ETF idea each day
- Rendered as a structured card between "What it means for you" and "Market-Moving Headlines"
- HTML: accent left-border card (`.one-trade-card` CSS class)
- Email: renders as plain `<h2>` / `<strong>` / `<em>` — no changes to email_sender.py needed
- LinkedIn: leads the post (replaces the data-driven title hook); body paragraphs dropped for brevity
- X thread: tweet 3/4 is now The One Trade with ✓/✗ markers for confirms/risk

### Claude-written email subject
New 6th JSON key: `email_subject` — 55–70 char subject leading with "The One Trade: {ticker} {direction} — {signal}".
- Written to `output/title_YYYY-MM-DD.txt` **during `--md-only`** (was previously skipped until publish phase)
- `send_email.py` already reads this file — no changes needed there
- `generate_market_day_break.py`: title write moved before `--md-only` early return

### Web page title
`daybreak_build_site.py` `<title>` now uses `ctx.get("email_subject")` so the browser tab reflects The One Trade.

**Why:** The Positioning Notes were 3–5 equally-weighted bullets with no focal point. The One Trade gives readers a single actionable call they can act on in 60 seconds, and makes the email subject compelling enough to open.
