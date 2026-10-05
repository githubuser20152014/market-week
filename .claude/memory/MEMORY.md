# Market Week — Workflow Memory

> **SYNC NOTE:** This file exists in two places. When updating either, always write to both:
> - Repo (version-controlled): `.claude/memory/MEMORY.md`
> - Global (Claude reads this): `~/.claude/projects/C--Users-Akhil-Documents-cc4e-course-market-week/memory/MEMORY.md`

## Verified Spot-Check Prices
- **2026-03-04**: Gold (GC=F) ~$5,204 confirmed. S&P 500 ~6,817, Nasdaq ~22,517, Dow ~48,501, 10Y ~4.056%, USD Index ~98.84.

## Fixture Data Workflow
- [fixture_verification.md](fixture_verification.md) — verify all prices against 2+ independent sources before writing any fixture file; confidence levels (High/Medium/Estimated); Feb 21 incident where fabricated equity values were ~10% off

## Architecture / Pipeline Notes
- [architecture_notes.md](architecture_notes.md) — chart/PDF filename prefix params, hosting (GitHub Pages via Porkbun DNS), site rebuild steps, explicit index.html links, fundaa date filter, stale fixture warning, --verify flag

## Market IQ Flashcards
- [market_iq_flashcards.md](market_iq_flashcards.md) — indicator term → anchor hyperlink mapping, live data-sourcing rule, update cadences

## System Overview Diagram
- `weekly-newsletter/output/system-overview.html` (last updated 2026-03-13) — open in browser, Ctrl+P → Save as PDF; update when a new content type/channel/integration is added, and bump the footer date

## Global Investor Edition
- [project_global_skill_rearchitect.md](project_global_skill_rearchitect.md) — /global rearchitected 2026-04-18: Haiku fetch + Sonnet orchestrate + Haiku publish; --pub-date flag; fixture check uses DATA_DATE
- [project_global_publish_incident_2026-07-25.md](project_global_publish_incident_2026-07-25.md) — recurring: publish corrupted same 8 historical pages 3x (07-25, 08-08, 08-16); 8 approved .md files missing from output/, will keep recurring until fixed
- [feedback_publish_weekly_two_step.md](feedback_publish_weekly_two_step.md) — STALE: claimed --publish never regenerates/no email; contradicted by code, see incident memory above
- [feedback_global_template_format.md](feedback_global_template_format.md) — approved MD + Substack HTML format; 13 LLM keys; macro regime as bullet list; no data tables in Substack
- [feedback_global_edition_tone.md](feedback_global_edition_tone.md) — cheeky/irreverent tone, plain-English analogies, ETF tickers, bold formatting; March 21 2026 edition is the reference
- [feedback_global_edition_title.md](feedback_global_edition_title.md) — generate 4-5 title options, ask user to pick before publishing
- [reference_substack_global.md](reference_substack_global.md) — Substack URL: frameworkfoundrymarket.substack.com
- Full end-to-end checklist: `weekly-newsletter/content/checklist_global_edition.md`
- Web live since 2026-04-11.

## The Blueprint — Wednesday Investing Series
- [project_blueprint_series.md](project_blueprint_series.md) — series overview, audience, file locations, launch status (Issue #2 written, not yet published)
- [feedback_blueprint_writing_approach.md](feedback_blueprint_writing_approach.md) — what to read before drafting, how to connect issues, how to anticipate reader questions

## Test Email Address
- [feedback_test_email_address.md](feedback_test_email_address.md) — "send me a test email" → cmgogo.miscc@gmail.com

## Subscriber Feedback Email
- [project_subscriber_feedback_email.md](project_subscriber_feedback_email.md) — file saved, tested, send command ready (not yet sent)

## Friday Fundaa — Pipeline
- [project_friday_fundaa_pipeline.md](project_friday_fundaa_pipeline.md) — publish status table by date/topic; source files `content/articles/friday-fundaa-*.md`; publish via `build_combined_site.py`
- [feedback_whatsapp_tone.md](feedback_whatsapp_tone.md) — punchy, cheeky, irreverent, dry humor + emoji; not a condensed Substack

## Weekly Edition
- [project_weekly_tone_update.md](project_weekly_tone_update.md) — apply Daybreak redesign (tables removed, "The Brief" merge, punchy tone) before next weekend run

## Morning Brief Redesign (2026-03-25)
- [project_morning_brief_redesign.md](project_morning_brief_redesign.md) — bold callouts, two-section split (The Brief / What it means for you), One Trade card, Claude-written subject wired to email + web title + LinkedIn + X
- [feedback_morning_brief_content_source.md](feedback_morning_brief_content_source.md) — once any edition MD is approved, it is the single content source; never regenerate, never touch previously published editions

## Daybreak
- [feedback_daybreak_tone.md](feedback_daybreak_tone.md) — cheeky/irreverent/dark humor, sarcastic observation after each data point, lead with contradiction; 2026-05-08 narrative reference, 2026-04-23 One Trade structure reference
- [feedback_daybreak_title_style.md](feedback_daybreak_title_style.md) — title must have a number + contradiction + punch; generate 5 options, user picks
- [feedback_daybreak_daily_fetch_scope.md](feedback_daybreak_daily_fetch_scope.md) — exact IS/ISN'T fetch scope; econ calendar + Market IQ card data excluded
- [feedback_daybreak_no_econ_calendar.md](feedback_daybreak_no_econ_calendar.md) — econ calendar removed from fetch/HTML/prompt; weekly/global unaffected
- [feedback_no_pdf.md](feedback_no_pdf.md) — skip PDF for daily edition; ignore verify_site_content.py PDF-missing failures
- `weekly-newsletter/content/checklist_daybreak_daily.md` — living daily-publish checklist, update when process changes
- [project_daybreak_scheduler_conflict_2026-08-10.md](project_daybreak_scheduler_conflict_2026-08-10.md) — UNRESOLVED: unidentified external process runs pipeline + headless polish on live dates, overwrote an in-progress human review; check file mtime/scheduler.log before trusting Daybreak drafts mid-session

## Social Post Standards
- [feedback_daybreak_social_post_standards.md](feedback_daybreak_social_post_standards.md) — X thread / LinkedIn / Substack note structure; email subject must reference The One Trade
- [feedback_no_stock_recs_social.md](feedback_no_stock_recs_social.md) — NO stock picks/entry-exit/directional calls in LinkedIn or X; macro narrative only, CTA to Substack
- [feedback_daybreak_substack_first.md](feedback_daybreak_substack_first.md) — publish Substack first; swap URL in X/LinkedIn to live note URL; CTA "Read on Substack", never "Full breakdown"
- [feedback_linkedin_substack_url.md](feedback_linkedin_substack_url.md) — LinkedIn CTA uses frameworkfoundrymkt.substack.com root domain, not full note URL
- [feedback_substack_one_trade_heading.md](feedback_substack_one_trade_heading.md) — `$TICKER` in the One Trade h2 must be a Yahoo Finance `<a>`, never plain text
- [feedback_substack_header.md](feedback_substack_header.md) — every post opens `<h1>[title]</h1>` then `<p><em>The Morning Brief · Market intelligence at the open</em></p>`
- [feedback_no_em_dash.md](feedback_no_em_dash.md) — replace — with " - " everywhere (all editions, prose/headers/tables)
- [feedback_email_and_substack_format.md](feedback_email_and_substack_format.md) — subscriber emails need Framework Foundry banner; Substack content must be HTML
- [feedback_publish_preserves_social_posts.md](feedback_publish_preserves_social_posts.md) — `--publish` regenerates substack/linkedin/X/title files; restore approved versions after site build if hand-crafted posts exist

## Publishing Safety
- [feedback_publish_timing.md](feedback_publish_timing.md) — writing/committing content is fine; never run build scripts or push until explicitly told to publish
- [feedback_past_editions.md](feedback_past_editions.md) — always ask before any change affects previously published editions
- [feedback_no_auto_email.md](feedback_no_auto_email.md) — never send subscriber emails automatically; draft files only, send requires explicit ask every time

## Workflow Preferences
- End-of-session commit: ask "Ready to commit the code changes to GitHub?" before committing source code — `publish.py --daybreak` auto-commits generated content, but source changes need separate explicit sign-off.

## Expat Magazine
- [project_expat_magazine_issue02.md](project_expat_magazine_issue02.md) — Issue 02 (Spain) live 2026-04-21, missing OG image, content review pending
