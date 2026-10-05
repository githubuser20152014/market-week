---
name: global-investor-edition-publish-incident-2026-07-25
description: "Publish step corrupted historical global edition pages three times (07-25, 08-08, 08-16); latest root cause is 8 dates missing their approved .md source entirely, so it will keep recurring on every full rebuild"
metadata: 
  node_type: memory
  type: project
  originSessionId: e03b998a-3cab-497f-abac-389a5dd8f548
  modified: 2026-08-16T11:51:50.520Z
---

On 2026-07-25 (Saturday publish, DATA_DATE 2026-07-24 per the weekend rule),
running the `global-publish` skill (which shells out to
`bash weekly-newsletter/publish_weekly.sh $DATE --global-only --publish`)
caused a real production incident. Root causes, verified directly against
the source at the time:

1. **`publish_weekly.sh` line ~74** calls `generate_global_newsletter.py
   --date "$DATE_STR"` unconditionally on every run. Since no fixture existed
   for `global_equity_2026-07-25.json` (our DATA_DATE was 07-24, not 07-25),
   `_live_flag()` returned `--live`, triggering a fresh yfinance fetch *and*
   a second Claude API call for date 2026-07-25. This produced a brand-new,
   unapproved narrative (different title, `$XLE` instead of the user's
   approved `$USO` One Trade) and silently overwrote
   `output/global_newsletter_2026-07-25.md`.
2. **`build_combined_site.py`'s `_override_global_ctx_from_md()`** matches
   section headings by exact string (`"Equity Markets"`, `"The One Trade"`,
   etc.) but the approved markdown's actual headings carry descriptive
   suffixes (`"Equity Markets - Europe Gains as US Tech Rout Deepens"`) and
   different casing (`"What it means for you"` vs `"What This Means For
   You"`). The override silently no-ops on mismatch, and the full site
   rebuild step then flattened **14 previously-published edition pages**
   (2026-04-24 through 2026-06-28) to generic placeholder sentences
   ("Equity markets showed regional divergence across US, Europe, and
   Asia-Pacific.") — this bug is presumably present on every edition using
   this heading style, it's just normally masked because the
   freshly-generated default content already matches before any human edits
   change the narrative.
3. The rebuild also created a **spurious duplicate edition page** at
   `site/global/2026-07-24/index.html` (the data date, not a real publish
   date) and added it to the site's archive table.
4. **`publish_weekly.sh` line ~134** calls `send_email.py --edition global`
   unconditionally after a successful push — not gated by `--global-only`
   the way US/intl are. The wrong content was confirmed sent to all 12
   addresses in `config/subscribers.txt`.
5. All of the above was committed (`2706ad7`) and pushed to `origin/master`
   automatically by the Haiku `global-publish` sub-agent, live on
   frameworkfoundry.info, before the human ever saw the regenerated content.

**Recovery performed** (commit `dd8410d`): restored the approved `.md` from
conversation context (had the exact pre-edit and post-edit text from the
review/edit steps), restored the 14 historical pages via
`git checkout 73e33bd -- <path>` (the commit right before the incident),
deleted the spurious 07-24 page + its unused 07-25-dated fixtures, manually
patched just the narrative blocks in the 07-25 site page to match the
approved markdown (did NOT re-run `build_combined_site.py`, since it would
risk re-triggering the same heading-match bug on the just-restored pages),
and pushed the fix.

**A drafted correction email** is at
`weekly-newsletter/output/global_correction_email_2026-07-25.md` — draft
only, never sent, per [[feedback_no_auto_email]].

**How to apply:**
- Do not trust the `global-publish` skill / `publish_weekly.sh --publish` to
  be regeneration-safe until someone actually patches (1) the unconditional
  `generate_global_newsletter.py` call and (2) the heading-match bug in
  `_override_global_ctx_from_md()`. See [[feedback_publish_weekly_two_step]]
  for the exact line-level detail (now corrected to match reality).
- Before publishing any weekend edition where DATA_DATE != PUB_DATE, verify
  a fixture exists for the literal PUB_DATE string too, or expect
  regeneration.
- If a bad publish happens again: check `git show --stat <bad-commit>` for
  the full blast radius before assuming it only touched the current date —
  this incident touched 14 unrelated historical pages.

**UPDATE 2026-08-08 — root causes patched, but 8 pages were still sitting
corrupted (uncommitted) and got re-pushed:**

Verified directly against source on 2026-08-08: all three original root
causes are now fixed. `publish_weekly.sh --publish` no longer calls
`generate_global_newsletter.py` at all when an approved `.md` exists (it
errors out instead if one is missing). `_override_global_ctx_from_md()` now
prefix-matches headings case-insensitively, correctly handling descriptive
suffixes. The global subscriber email is gated behind an explicit
`--send-email` flag, separate from `--global-only`. So the skill is safe to
run again under normal conditions.

However: 8 of the original 14 flattened pages (2026-04-24, 05-01, 05-08,
05-15, 05-29, 06-05, 06-12, 06-27 — the other 6 from the original 14 must
have been separately fixed at some point) were **still sitting corrupted,
uncommitted, in the working tree** at the start of the 2026-08-08 session,
visible in `git status` as pre-existing `M` entries before any action was
taken this session. `publish_weekly.sh`'s `git add weekly-newsletter/site/`
stages the *entire* site directory unconditionally, so publishing the
2026-08-08 edition swept this stale corruption into the publish commit
(`9ab9a8b`) and pushed it live again. Fixed in `09032d2` via
`git checkout 6b9ac6d -- <paths>` (last known-good commit) + recommit + push.

**Updated how to apply:**
- Before running any `--publish` step, run `git status` on
  `weekly-newsletter/site/` first. If there are pre-existing modified files
  unrelated to today's date, investigate and resolve them *before*
  publishing — `publish_weekly.sh` will stage and commit whatever is sitting
  in that directory, good or bad, with no filtering by date.
- After every publish, run `git show --stat HEAD` and check every changed
  historical page's diff, not just the current date's. A one-line title
  check (`grep big-theme-title`) against a couple of older editions is a
  fast smoke test for the placeholder-flattening pattern specifically.

**UPDATE 2026-08-16 — same 8 pages flattened a third time, new root cause
found: the approved `.md` source files for those 8 dates don't exist:**

Pre-flight `git status` was clean (per the guidance above) before running
the 2026-08-15 `/global` publish. The heading-match fix from the 2026-08-08
update was confirmed present in `build_combined_site.py` at the time. The
publish still re-flattened the same 8 pages
(2026-04-24, 05-01, 05-08, 05-15, 05-29, 06-05, 06-12, 06-27) and committed
it live in `fd6cd50`, caught by the post-publish `git show --stat HEAD`
check from the 2026-08-08 update — which is why that check earns its keep.

**Real root cause, verified directly:** `weekly-newsletter/output/` has no
`global_newsletter_<date>.md` file for any of those 8 dates — confirmed with
`ls` per date, all 8 return "No such file". The heading-match fix in
`_override_global_ctx_from_md()` was never the actual problem for these
specific pages; there is no `.md` for it to match against in the first
place, so the full-site rebuild has nothing to override the generic default
context with, and it writes placeholder narrative every single time it
runs, regardless of any heading-matching logic. The 2026-08-08 fix likely
*does* correctly stop *new* incidents of the original bug (live regeneration
producing a differently-headed `.md`), but it cannot fix these 8, because
their source `.md` simply isn't there to parse.

**Recovery performed** (commit `c540939`): `git checkout 09032d2 -- <paths>`
for all 8 pages (last known-good commit from the 2026-08-08 recovery), did
NOT re-run `build_combined_site.py`, committed and pushed directly. Did not
attempt to recover or recreate the missing `.md` files themselves.

**Updated how to apply:**
- The `git status` pre-flight check on `weekly-newsletter/site/` and the
  post-publish `git show --stat HEAD` check are both still necessary, but
  **not sufficient** — this incident had a clean pre-flight and still
  recurred. The post-publish check remains the real safety net; always run
  it, every time, and always check *all* changed historical pages, not just
  today's.
- This bug will keep recurring on **every** `/global` publish that does a
  full site rebuild, for as long as these 8 `.md` files are missing from
  `output/`. It is not a one-time fluke.
- Real fix needs one of two things, not yet done as of this update: (a)
  recover/recreate the 8 missing `.md` files so the override has a real
  source, or (b) patch `build_combined_site.py` so a missing `.md` leaves
  the existing page untouched instead of falling back to placeholder
  content. Until one of those lands, expect to repeat this same manual
  `git checkout 09032d2 -- <paths>` recovery after every future publish.
