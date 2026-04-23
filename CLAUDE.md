# CLAUDE.md — Market Week (Daybreak Newsletter Pipeline)

## What this repo is

The Daybreak newsletter pipeline. Publishes Monday–Friday, 6–7 AM window. Daily market intelligence brief for serious ETF investors: yesterday's US close + overnight Asia/Europe + pre-market futures + one high-conviction trade.

## Architecture (3-phase)

```
Phase 1 — Generate (Haiku fetches data, Sonnet writes narrative)
  bash weekly-newsletter/publish_daybreak.sh DATE
  → Haiku: fetches market data → saves fixture (daybreak_DATE.json)
  → Claude Sonnet API: generates narrative, plain_summary, positioning, one_trade
  → Outputs: output/market_day_break_DATE.md
  → STOPS. Human reviews the markdown.

Phase 2 — Publish (Haiku builds site + git push)
  bash weekly-newsletter/publish_daybreak.sh DATE --publish
  → Reads approved .md (does NOT call Claude API again)
  → Generates social posts from approved content
  → Builds site, git push, email preview

Phase 3 — Send
  bash weekly-newsletter/publish_daybreak.sh DATE --send-email
  → Sends to subscriber list via Gmail SMTP
```

## Key files

```
weekly-newsletter/
├── publish_daybreak.sh                   ← Shell orchestrator (entry point)
├── generate_market_day_break.py          ← Python coordinator
├── data/
│   ├── fetch_daybreak_data.py            ← yfinance + Finnhub + Perplexity
│   ├── daybreak_process_data.py          ← Claude API call + content generators
│   │   └── _DAYBREAK_SYSTEM_PROMPT       ← The Claude system prompt (edit here for tone)
│   └── email_sender.py                   ← Gmail SMTP
├── output/
│   └── market_day_break_DATE.md          ← The approved newsletter (human-reviewed source)
├── fixtures/
│   └── daybreak_DATE.json                ← Saved live data (written once)
└── config/
    ├── api_keys.env                       ← ANTHROPIC_API_KEY, GMAIL_*, FINNHUB_*
    └── subscribers.txt                    ← One email per line
```

## Voice and tone (mandatory — applies to all content work in this repo)

The reader is a serious ETF investor. Not a trader. Not a beginner. They want signal, not noise.

**The voice:** Portfolio manager briefing a colleague before the open. Direct. Short sentences. Named catalysts with exact numbers. No hedging.

**Em dashes (—) are banned.** Use a colon for elaboration, comma for a parenthetical aside, period where two thoughts stand alone.

**Banned phrases:** "amid concerns", "market participants remain cautious", "volatility persists", "investors digest", "risk sentiment". Name the specific actor, catalyst, and price move.

**The one_trade thesis** starts with the signal or anomaly, not the action. The asymmetry should be obvious in one sentence.

**Bold callouts in plain_summary:** 6–10 highlights. Price figures at inflection points, named catalysts, cross-asset tension phrases. Not decorative — reward scanning.

## Skills

- `/daybreak DATE` — full Daybreak production run with review checkpoints
- `/daybreak-fetch DATE` — data collection only (Haiku sub-agent)
- `/daybreak-publish DATE` — publish + email preview (Haiku sub-agent)

## Common commands

```bash
# Run generate phase only (review before publishing)
bash weekly-newsletter/publish_daybreak.sh 2026-04-23

# Publish after approving the markdown
bash weekly-newsletter/publish_daybreak.sh 2026-04-23 --publish

# Send email to subscribers
bash weekly-newsletter/publish_daybreak.sh 2026-04-23 --send-email
```

## Critical invariant

The approved `.md` file is the single source of truth for Phase 2. Nothing is regenerated from raw data after human approval. The Claude API is called exactly once (Phase 1). Phase 2 reads from the markdown via `_override_from_approved_md()`.
