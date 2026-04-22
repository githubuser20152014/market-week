---
name: Global Investor Edition — template and Substack format reference
description: Approved format for global newsletter MD and Substack HTML, based on April 11 2026 reference edition
type: feedback
originSessionId: 834d9566-ac98-4c2d-8cdc-1faf662ae69e
---
## Markdown template (`templates/global_newsletter_template.md`)

- No "Page 1 / Page 2 / Page 3" section headers — removed entirely
- Section headings include LLM-generated subtitles: `### Equity Markets - [subtitle]`
- **The One Trade section** appears before Global Investor Positioning
- Data appendix: no "Week Range" column — just Close and Weekly %
- Fixed Income rows (10Y Treasury, USD Index) merged into the Commodities & Fixed Income table — no separate Fixed Income table
- Header title uses ` - ` not `—`: `# Framework Foundry Weekly - Global Investor Edition`

## LLM prompt (`data/process_global_data.py` — `_GLOBAL_SYSTEM_PROMPT`)

Now requests 13 JSON keys (up from 8):
- Added: `equity_subtitle`, `fx_subtitle`, `commodities_subtitle`
- Added: `one_trade_ticker`, `one_trade_direction`, `one_trade_body`
- `max_tokens` raised from 2048 → 4096 (2048 caused JSON truncation at ~7700 chars)
- Model: `claude-sonnet-4-6` (was `claude-opus-4-6`, which is not a valid model ID)

## Substack HTML format (`output/global_substack_DATE.html`)

Reference: `output/global_substack_2026-04-11.html`

Key differences from auto-generated HTML:
- **Macro Regime**: `<ul>` bullet list format `<li><strong>Growth · GREEN</strong> - note</li>` — NOT a table
- **No data tables** — narrative only; data lives on the web version
- Footer has "Full data tables" link BEFORE the editions list
- One Trade Confirms/Risk: single `<p>` with `<br>` between them (not separate `<p>` tags)
- Header: `Framework Foundry - Global Investor Edition | DATE` (hyphen, not em-dash)

`build_global_substack.py` does NOT produce the correct format — write the Substack HTML manually from the approved MD content.

**Why:** The `build_global_substack.py` auto-generator produces tables for macro regime and includes full data tables, which don't match the approved Substack format used since April 11.
