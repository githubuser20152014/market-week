---
name: Weekly edition tone + layout update pending
description: Apply the same Daybreak narrative redesign and tone changes to the weekly edition generators before the next weekend run
type: project
---

Apply the same changes made to the Daybreak edition to the weekly edition.

**Why:** Daybreak was redesigned week of 2026-03-16 — tables removed, narrative sections merged into "The Brief", tone rewritten to match Akhil's style (short declarative sentences, "Not X — Y" flips, no hedging, punchy). Weekly should be consistent.

**How to apply:** When user says "run the weekly" or on a weekend session, prompt to do these edits first:

1. `templates/newsletter_template.md` (or equivalent weekly template) — remove data tables, merge narrative sections into a single "The Brief" block, trim headlines to 5
2. `data/process_data.py` (weekly equivalent of `daybreak_process_data.py`) — rewrite the narrative/plain_summary para-builder functions with the same tone: short sentences, name the thing directly, no filler, dry wit
3. `build_site.py` (weekly HTML builder) — same structural change as `daybreak_build_site.py`: merge Morning Brief + What This Means into single "The Brief" section, remove data table blocks
4. Social generators (LinkedIn, X, Substack) in weekly process_data — same stale string fixes as Daybreak
5. Positioning tips fallbacks — same tone tightening

**Reference:** Daybreak changes made in session 2026-03-16. See `daybreak_build_site.py`, `data/daybreak_process_data.py`, `templates/daybreak_template.md` for the exact pattern to follow.
