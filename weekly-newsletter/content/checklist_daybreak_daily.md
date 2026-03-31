# Market Day Break — Daily Publish Checklist

Run every **weekday morning** for that day's date (YYYY-MM-DD).
Last updated: 2026-03-31

---

## What the automated run does (5:15 AM EST)

Windows Task Scheduler fires `publish_daybreak.sh DATE` automatically.

- Fetches live data: US closes, APAC overnight, FX, futures, news headlines
- Verifies prices against FRED (10Y Treasury crosscheck)
- Saves `fixtures/daybreak_DATE.json`
- Calls Claude API once → writes draft `output/market_day_break_DATE.md`
- Runs headless polish pass (sharpens teaser + positioning notes)
- Stops. Output logged to `output/daybreak_scheduler.log`

**Not fetched by the automated run:**
- Economic events calendar (removed — slow, buggy, not relevant to daily readers)
- Market IQ card data (updates monthly/per-FOMC, not daily)

---

## Step 1 — Review the draft (you)

- [ ] Open `output/market_day_break_DATE.md`
- [ ] Check the teaser / narrative — does it capture the right story?
- [ ] Check The One Trade — ticker, direction, thesis, confirm, risk all make sense?
- [ ] Check Positioning Notes — are the conditions specific and actionable?
- [ ] Check all prices and % figures — spot-check against a live source
- [ ] Make any edits directly to the `.md` file
- [ ] Save. This file is now the approved content source — no further Claude API calls

---

## Step 2 — Publish to web

```bash
bash weekly-newsletter/publish_daybreak.sh DATE --publish
```

What this does (no Claude API calls):
- Reads approved `.md` → populates narrative, one trade, tips
- Generates LinkedIn post → `output/linkedin_DATE.txt`
- Generates X thread → `output/x_DATE.txt`
- Generates Substack draft → `output/substack_DATE.html`
- Builds site HTML from approved `.md` via `build_combined_site.py`
- Commits + pushes → GitHub Pages deploys automatically

- [ ] Verify live at `https://frameworkfoundry.info/daily/DATE/`
- [ ] Review X thread — Tweet 1 hooks with the anomaly (no data table), Tweet 2 "Here's my read:" expresses the thesis, Tweet 3 is The One Trade with $TICKER cashtag, Tweet 4 says "Read on Substack"
- [ ] Review LinkedIn post — leads with The One Trade, followed by "Here's why:" + macro driver paragraph + investor implication, ends with "Read on Substack →"
- [ ] Review Substack note (`output/substack_DATE.html`) — title is "The One Trade: DIRECTION $TICKER — [hook clause]", hook breaks into punchy short paragraphs, "Here's my read:" macro thesis, One Trade block, "What else I'm watching" bullets
- [ ] **Publish the Substack note** (paste `substack_DATE.html` into Substack editor and post)
- [ ] **Swap the URL** in `output/x_DATE.txt` and `output/linkedin_DATE.txt` — replace the default frameworkfoundry.info link with the live Substack note URL
- [ ] Update the CTA text if needed — should say "Read on Substack" not "Full breakdown"

---

## Step 3 — Review email preview

- [ ] Open `output/email_preview_DATE.html` in browser
- [ ] Check subject line (from `output/title_DATE.txt`) — **must be punchy and reference The One Trade (ticker + direction)**
- [ ] Check email body — narrative, one trade card, positioning notes look right?
- [ ] If changes needed: edit the `.md`, re-run Step 2

---

## Step 4 — Send email

```bash
bash weekly-newsletter/publish_daybreak.sh DATE --send-email
```

- [ ] Confirm send
- [ ] Check inbox (cmgogo.miscc@gmail.com) for test receipt

---

## If the automated run crashed

Check `output/daybreak_scheduler.log` for the error. Common causes:

- **PriceDiscrepancyError (10Y Treasury)** — yfinance and FRED disagree >2%. Run `/daybreak DATE` manually; Perplexity will resolve the correct value.
- **FRED timeout** — transient. Re-run; verification will pass or skip gracefully.
- **No fixture, no MD** — run `/daybreak DATE` manually to generate from scratch.

---

## Guardrails (never do these)

- Do NOT re-run the generator after approving the `.md` — it will overwrite your edits
- Do NOT run `--publish` before reviewing the `.md` — the script will error if the file is missing
- Do NOT touch previously published editions without explicit confirmation
- Do NOT fetch economic calendar or Market IQ card data as part of the daily run
