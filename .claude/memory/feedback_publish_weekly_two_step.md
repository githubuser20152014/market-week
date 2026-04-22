---
name: publish_weekly.sh — generation and publish are strictly separated
description: --publish flag never regenerates content; approved MD files are the single source of truth
type: feedback
originSessionId: 834d9566-ac98-4c2d-8cdc-1faf662ae69e
---
`publish_weekly.sh` now enforces a hard two-step workflow:

**Step 1 — generate only (no --publish flag):**
```bash
bash publish_weekly.sh DATE --global-only
```
Runs generators, writes markdown files, exits. No site build, no commit, no push.

**Step 2 — publish only (--publish flag):**
```bash
bash publish_weekly.sh DATE --global-only --publish
```
Skips ALL generation. Goes straight to: build site → stage → commit → push. Never touches markdown files.

**No email sending** — the `send_email.py` calls were removed entirely from the script. Email is no longer part of any automated publish flow.

**Why:** In a prior session, running --publish re-ran `generate_global_newsletter.py` which called the Claude API and overwrote the user's approved ceasefire narrative with generic LLM output. The approved MD file is the single content source — once reviewed, it must never be regenerated.

**How to apply:** Never add generation steps back into the --publish path. If content needs regenerating, that's a separate explicit step before publish.
