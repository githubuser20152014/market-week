---
name: publish_weekly.sh — generation and publish are strictly separated
description: "STALE CLAIM below is contradicted by current code (verified 2026-07-25) — publish_weekly.sh regenerates and emails unconditionally"
type: feedback
originSessionId: 834d9566-ac98-4c2d-8cdc-1faf662ae69e
modified: 2026-07-25T11:36:59.742Z
---

**STATUS UPDATE (2026-07-25): the fix described below did not hold.** Read
[[project_global_publish_incident_2026-07-25]] first — verified against the
actual source of `weekly-newsletter/publish_weekly.sh` on 2026-07-25:

- Line ~74 calls `python generate_global_newsletter.py --date "$DATE_STR" ...`
  **unconditionally**, regardless of whether `--publish` is passed. If no
  fixture exists for `$DATE_STR` (e.g. because DATA_DATE != PUB_DATE on a
  weekend edition), this triggers `--live` fetch + a fresh Claude API call,
  silently overwriting the human-approved markdown with new unapproved
  content.
- Line ~134 calls `python send_email.py --edition global --date "$DATE_STR"`
  **unconditionally** after a successful push, with no flag to skip it. It is
  NOT gated by `--global-only` the way the US/intl email calls are (lines
  ~130-133 check `GLOBAL_ONLY` first; the global one does not).

Do not trust the "no email sending" / "never regenerates" claims below
without re-reading the actual script first — this file describes intent from
a prior fix attempt, not current behavior.

**Original (now-contradicted) note, kept for history:**

`publish_weekly.sh` was believed to enforce a hard two-step workflow:

Step 1 — generate only (no `--publish` flag): runs generators, writes
markdown, exits. Step 2 — publish only (`--publish` flag): skips generation,
goes straight to build → stage → commit → push. "No email sending" — the
`send_email.py` calls were believed removed entirely.

**Why this mattered originally:** in an earlier session, running `--publish`
re-ran `generate_global_newsletter.py`, which called the Claude API and
overwrote the user's approved ceasefire narrative with generic LLM output.

**How to apply now:** before running `/global-publish` or
`publish_weekly.sh ... --publish` for any date, confirm fixtures already
exist for that exact `$DATE_STR` (not just DATA_DATE if it differs from
PUB_DATE) — otherwise the script will regenerate. Treat the "no email"
assumption as false until the script is actually patched; assume email WILL
send on any successful global publish run.
