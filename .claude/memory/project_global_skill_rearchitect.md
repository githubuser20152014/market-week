---
name: Global skill three-phase rearchitect (2026-04-18)
description: /global rearchitected into Haiku fetch + Sonnet orchestrator + Haiku publish, matching /daybreak pattern
type: project
originSessionId: 834d9566-ac98-4c2d-8cdc-1faf662ae69e
---
## What was built

Three skill files implement the new architecture:
- `.claude/commands/global-fetch.md` — Haiku sub-skill; runs `fetch_and_verify_global.py --date DATE`; returns structured STATUS/FLAGGED_ASSETS/SUMMARY/NOTES report; no user interaction
- `.claude/commands/global-publish.md` — Haiku sub-skill; runs `publish_weekly.sh DATE --global-only --publish`; returns STATUS/SUBSTACK_FILE/X_THREAD_FILE/LINKEDIN_FILE/PUBLISH_NOTES
- `.claude/commands/global.md` — Sonnet orchestrator; Step 0 spawns global-fetch (Haiku), Steps 1-2 generate + review (Sonnet), Step 3 spawns global-publish (Haiku), Steps 4-5 display Substack HTML then social posts

## Saturday publication date handling

`generate_global_newsletter.py` now accepts `--pub-date YYYY-MM-DD` (separate from `--date`):
- `--date` = fixture/data date (Friday)
- `--pub-date` = display date in header + output filename (Saturday)

The orchestrator in `global.md` computes both: if today is Saturday, DATA_DATE = PUB_DATE - 1 day.

## Fixture check

Step 0 checks for all three fixtures using DATA_DATE (not PUB_DATE):
- `fixtures/global_equity_DATA_DATE.json`
- `fixtures/global_fx_DATA_DATE.json`
- `fixtures/global_commodity_DATA_DATE.json`

If all exist, skips fetch agent entirely.

**Why:** Mirrors /daybreak pattern for token efficiency — Haiku handles I/O, Sonnet handles narrative and user interaction.
**How to apply:** When running /global, always let the orchestrator compute PUB_DATE vs DATA_DATE automatically.
