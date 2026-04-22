# Market Week — Workflow Memory

> **SYNC NOTE:** This file exists in two places. When updating either, always write to both:
> - Repo (version-controlled): `.claude/memory/MEMORY.md`
> - Global (Claude reads this): `~/.claude/projects/C--Users-Akhil-Documents-cc4e-course-market-week/memory/MEMORY.md`

## Verified Spot-Check Prices
- **2026-03-04**: Gold (GC=F) ~$5,204 ✓ confirmed. S&P 500 ~6,817, Nasdaq ~22,517, Dow ~48,501, 10Y ~4.056%, USD Index ~98.84.

## Fixture Data Workflow

### REQUIRED: Verify all prices against 2 independent sources before writing any fixture file

When creating or updating any `fixtures/*.json` file with market prices:

1. **Look up each asset from at least 2 independent sources** (e.g., FRED, Yahoo Finance, CNBC, Investing.com, MarketWatch, Nasdaq.com, US Treasury H.15, pricegold.net).
2. **Cross-reference closing prices** — note any discrepancies between sources and flag them.
3. **Only use confirmed closes** — mark intraday open/high/low as "estimated" if not independently verified.
4. **Do not fabricate or extrapolate prices** — a plausible-looking number is not a correct number.

**Why this matters:** In the Feb 21 fixture, fabricated equity values were ~10% off (S&P 500: 6,205 vs actual 6,910; Dow: 45,312 vs actual 49,626; USD Index: 107.85 vs actual 97.80). Only gold was close because it was specifically researched.

### Confidence levels to record per asset
- **High**: closing price confirmed by 2+ primary sources (FRED, official exchange data)
- **Medium**: closing price confirmed by 1 primary source; mid-week values interpolated
- **Estimated**: open/high/low inferred from context when intraday data unavailable

---

## Architecture Notes

### generate_price_chart(prefix=)
`data/chart.py` accepts a `prefix` param (default `"chart"`). Always pass
`prefix="intl_chart"` when calling from `generate_intl_newsletter.py` to
avoid clobbering the US chart for the same date.

### generate_pdf(filename=)
`data/pdf_export.py` accepts a `filename` param (default `newsletter_{date}.pdf`).
Always pass `filename=f"intl_newsletter_{date_str}.pdf"` from the intl generator
to avoid clobbering the US PDF for the same date.

### Newsletter generation order
Running both generators for the same date is safe **only if** the above params
are used. The intl generator used to rename outputs, deleting the US files.

### Hosting
- **GitHub Pages** serves the site. Porkbun DNS forwards `frameworkfoundry.info` to GitHub Pages.
- NOT Cloudflare Pages. A `git push` to `origin/master` is all that's needed to deploy.

### Site rebuild workflow
1. Run `generate_newsletter.py --date YYYY-MM-DD --pdf --live --no-verify`
2. Run `generate_intl_newsletter.py --date YYYY-MM-DD --pdf --live` (if intl edition needed)
3. Run `build_combined_site.py`
4. Commit: `site/`, updated `output/` files, new `fixtures/` files
5. Push → GitHub Pages deploys automatically

**Critical:** Always use `--live` when generating for a new week. Both generators now
auto-save live yfinance data as fixture files (`indices_YYYY-MM-DD.json`, etc.) so
`build_combined_site.py` uses the same verified prices. Without `--live`, the site
builder falls back to the nearest old fixture and shows stale/wrong prices.

### Site links must use explicit index.html paths
`build_combined_site.py` generates links as `us/YYYY-MM-DD/index.html` (not trailing slash).
Trailing-slash directory links don't auto-load index.html over `file://` protocol.

### "What This Means" section
Both US and intl newsletters have a plain-English investor summary after "The Week in Brief".
- US: `generate_plain_english_summary()` in `data/process_data.py`
- Intl: `generate_intl_plain_english_summary()` in `data/intl_process_data.py`
- Template vars: `plain_summary` (both editions)
- Site HTML rendering: `build_site.py` (US), `intl_build_site.py` (intl)

### Fundaa date filter — allows 1 day ahead
`parse_fundaa_articles()` in `build_combined_site.py` filters articles to
`date <= today + timedelta(days=1)`. This lets a Friday article go live on
Thursday without waiting for the calendar to roll over.

### Stale fixture warning
`fetch_data.py` prints a WARNING if the closest fixture is >2 days from the
requested date. This means data is stale — use `--live` or create a new fixture.

## Market IQ Flashcards

### ACTIVE: Link economic indicator mentions to flashcards in every edition
Every mention of a tracked economic indicator in the newsletter HTML **must** be
hyperlinked to its flashcard entry. This applies to all future editions now.

Term → anchor mapping:
- "CPI" / "consumer price index" → `/market-iq#cpi`
- "NFP" / "non-farm payrolls" → `/market-iq#nfp`
- "yield curve" → `/market-iq#yield-curve`
- "Fed funds rate" / "FFR" / "federal funds rate" → `/market-iq#ffr`
- "PCE" / "personal consumption expenditures" → `/market-iq#pce`

Implementation notes:
- Add `id` anchors to each flashcard block (e.g. `id="cpi"`) when building the live page
- In `build_site.py` / `build_combined_site.py`, add a post-render pass that
  regex-replaces known indicator terms in the newsletter body with `<a>` tags
- Maintain a term→anchor mapping dict (covers abbreviations + full names +
  common press shorthand)
- Links should open the Market IQ page with the card pre-scrolled into view
  (anchor link) — no new tab needed since it's same-site navigation

### Go-live: use auto-pull for card data
When integrating Market IQ flashcards into the live site, card data must be
populated from the existing pipeline (`fetch_data.py` / FRED / yfinance fixtures)
— **not** hardcoded. The current `output/market-iq-flashcards_mockup.html` has
hardcoded values for review only.

Update cadences per card:
- CPI → monthly (~2nd Tuesday, BLS)
- FFR → 8× / year (FOMC decision days)
- NFP → monthly (1st Friday, BLS)
- PCE → monthly (~last Friday, BEA)
- Yield Curve → monthly snapshot (10Y & 2Y already in fixtures)

## System Overview Diagram

- **File:** `weekly-newsletter/output/system-overview.html`
- **Last updated:** 2026-03-13
- Open in browser and Ctrl+P → Save as PDF to share
- **Update this file when:** a new content type is added, a new distribution channel goes live, a major integration changes (e.g. Substack automated, LinkedIn API), or new data sources are added
- When updating, also bump the "Generated" date in the footer

## Global Investor Edition
- [project_global_skill_rearchitect.md](project_global_skill_rearchitect.md) — /global rearchitected 2026-04-18: Haiku fetch + Sonnet orchestrate + Haiku publish; --pub-date flag; fixture check uses DATA_DATE
- [feedback_publish_weekly_two_step.md](feedback_publish_weekly_two_step.md) — publish_weekly.sh: generation and --publish are strictly separated; --publish never regenerates; no email sending
- [feedback_global_template_format.md](feedback_global_template_format.md) — approved MD + Substack HTML format; 13 LLM keys; macro regime as bullet list; no data tables in Substack
- **2026-04-18**: Web live. Substack HTML written manually. X + LinkedIn pending.
- [project_global_2026-04-11.md](project_global_2026-04-11.md) — Web live 2026-04-11.
- [reference_substack_global.md](reference_substack_global.md) — Substack URL: frameworkfoundrymarket.substack.com
- Full end-to-end checklist: `weekly-newsletter/content/checklist_global_edition.md`

## The Blueprint — Wednesday Investing Series
- [project_blueprint_series.md](project_blueprint_series.md) — series overview, audience, file locations, launch status (Issue #2 written, not yet published)
- [feedback_blueprint_writing_approach.md](feedback_blueprint_writing_approach.md) — what to read before drafting, how to connect issues, how to anticipate reader questions

## Test Email Address
- [feedback_test_email_address.md](feedback_test_email_address.md) — "send me a test email" → cmgogo.miscc@gmail.com

## Subscriber Feedback Email — Ready to Send Thursday Evening
- [project_subscriber_feedback_email.md](project_subscriber_feedback_email.md) — file saved, tested, send command ready

## Friday Fundaa — Published & Pipeline

| Date | Topic | Status |
|------|-------|--------|
| 2026-03-13 | Shrinkflation | Live |
| 2026-03-20 | Stagflation | Live |
| 2026-03-27 | Yield curve | Written, not yet published |
| 2026-03-28 | WTI & Brent crude | Written, not yet published |
| 2026-04-04 | Tariffs (who actually pays?) | Written, not yet published |

Source files: `weekly-newsletter/content/articles/friday-fundaa-*.md`
To publish: run `build_combined_site.py`, commit `site/fundaa/YYYY-MM-DD/` + `site/index.html`, push.

## Pending: Weekly Edition Tone + Layout Update
- [project_weekly_tone_update.md](project_weekly_tone_update.md) — apply Daybreak redesign (tables removed, "The Brief" merge, punchy tone) to weekly edition before next weekend run

## Global Investor Edition — Content Style
- [feedback_global_edition_tone.md](feedback_global_edition_tone.md) — approved tone, plain-English analogies, ETF tickers, bold formatting, no page-number headings. Use March 21 2026 edition as the reference.
- [feedback_global_edition_title.md](feedback_global_edition_title.md) — generate 4-5 title options from article content, ask user to pick before publishing

## Morning Brief Redesign (2026-03-25)
- [project_morning_brief_redesign.md](project_morning_brief_redesign.md) — bold callouts, two-section split (The Brief / What it means for you), The One Trade card, Claude-written email subject wired to email + web title + LinkedIn + X
- [feedback_morning_brief_content_source.md](feedback_morning_brief_content_source.md) — once any edition MD is approved, it is the single content source; never regenerate, never run generators again, never touch previously published editions

## Daybreak — Daily Publish Checklist
- `weekly-newsletter/content/checklist_daybreak_daily.md` — living todo list for daily publish flow; update this file whenever the process changes

## Daybreak — Daily Fetch Scope
- [feedback_daybreak_daily_fetch_scope.md](feedback_daybreak_daily_fetch_scope.md) — exact list of what IS and ISN'T fetched each day; economic calendar and Market IQ card data are both excluded
- [feedback_daybreak_no_econ_calendar.md](feedback_daybreak_no_econ_calendar.md) — econ calendar removed from fetch, HTML, and Claude prompt; returns empty list; weekly/global unaffected

## Daybreak Publish — No PDF Needed
- [feedback_no_pdf.md](feedback_no_pdf.md) — skip PDF generation for daily edition; ignore verify_site_content.py failures about missing PDF

## Daybreak — Social Post Standards (updated 2026-03-31)
- [feedback_daybreak_social_post_standards.md](feedback_daybreak_social_post_standards.md) — X thread (anomaly hook → "Here's my read:" → $TICKER One Trade → Substack link), LinkedIn (One Trade → "Here's why:" → implication), Substack note (punchy paras, One Trade centrepiece, "What else I'm watching" bullets), email subject must reference The One Trade
- [feedback_daybreak_substack_first.md](feedback_daybreak_substack_first.md) — publish Substack note first; swap URL in X/LinkedIn from frameworkfoundry.info to live Substack note URL; CTA is "Read on Substack", never "Full breakdown"
- [feedback_linkedin_substack_url.md](feedback_linkedin_substack_url.md) — LinkedIn: use frameworkfoundrymkt.substack.com (root domain, not full note URL)

## Friday Fundaa — WhatsApp Tone
- [feedback_whatsapp_tone.md](feedback_whatsapp_tone.md) — punchy, cheeky, irreverent; give concepts personality; dry humor + emoji; not a condensed Substack

## Publishing Standards

- [No em dashes](feedback_no_em_dash.md) — replace — with " - " in all newsletter output (all editions, prose + headers + tables)
- [Email and Substack formatting](feedback_email_and_substack_format.md) — subscriber emails need Framework Foundry banner; Substack content must be HTML

## Publishing — Never Build or Deploy Without Being Asked
- [feedback_publish_timing.md](feedback_publish_timing.md) — writing and committing a content file is fine; never run build scripts or push to the web until the user explicitly says to publish

## Past Editions — Confirm Before Touching
- [feedback_past_editions.md](feedback_past_editions.md) — always ask before any change affects previously published editions

## Workflow Preferences

### End-of-session GitHub commit
When a session's work looks complete and content looks good, always ask:
"Ready to commit the code changes to GitHub?"
before committing source code. The `publish.py --daybreak` orchestrator auto-commits
generated content (fixtures, site), but source code changes should be committed
separately with explicit user sign-off.

---

### Price verification (--verify flag)
`generate_newsletter.py --live --verify` cross-checks yfinance prices against FRED + Stooq before generating. Raises `PriceDiscrepancyError` if any asset diverges >2%.

---

## Expat Magazine — Issue 02 (Spain)

### 2026-04-21 — Publication wrap-up

**Done:**
- Added Issue 02 (Spain) card to `_EXPAT_PANEL` in `build_combined_site.py`
- Regenerated `site/index.html` with new Issue 02 card
- Committed and pushed to GitHub Pages — now live at https://frameworkfoundry.info/index.html#expat
- Both Issue 01 (Portugal) and Issue 02 (Spain) appear as clickable cards in the Expat Investing section

**Open/Blocked:**
- [ ] **Missing OG image:** `site/expat/issue-02/og-image.jpg` does not exist. File is referenced in `<meta property="og:image">` but not present. Social sharing previews (Twitter/WhatsApp) will fail until this is added.
- [ ] **Thin content / missing pictures:** The Spain Issue HTML exists but content appears sparse and images may be missing or incomplete. Recommend review of visual assets before considering the magazine fully launched.

**Next steps:**
1. Add OG image (og-image.jpg) to `site/expat/issue-02/` — suggest Spain/Valencia themed image matching Issue 01 structure
2. Review Issue 02 content for completeness — verify all charts, images, and visual elements render properly
3. Test social sharing on Twitter/LinkedIn to confirm OG image displays once added
