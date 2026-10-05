---
name: Publish step must not overwrite approved social posts
description: The --publish step regenerates social files from templates, clobbering any hand-crafted versions
type: feedback
originSessionId: a85b9ce0-aa4c-46a0-bc74-49271a0e2702
modified: 2026-08-27T10:17:22.493Z
---
The `--publish` flag in `publish_daybreak.sh` runs `generate_market_day_break.py --no-rewrite-md`, which regenerates substack HTML, LinkedIn, X, and title files from scratch using the Claude API. This overwrites any hand-crafted or user-approved versions of those files.

**Why:** Discovered 2026-04-23: after crafting edgy, opinionated social posts with the user, the publish step silently replaced all of them with auto-generated defaults.

**How to apply:** Whenever social posts have been hand-crafted and approved by the user before the publish step:
1. Save copies of the approved files before running `--publish`
2. After the publish step completes (site built, pushed), restore the approved social files
3. Commit the restored files separately with a note like "Restore approved social posts"

Alternatively: run the site build manually (just `build_combined_site.py` + verify + commit/push) to avoid triggering social post regeneration entirely.

**2026-08-27 update:** the `/daybreak` skill's Step 5 restore instructions only name substack/linkedin/x — they omit `title_DATE.txt`, but publish regenerates and overwrites the title too (confirmed: reverted the user's approved title back to an auto-generated one with a banned em dash, and the bad title also leaked into `email_preview_DATE.txt`'s `<title>` tag, though not into the live site page body). Always restore `title_DATE.txt` alongside the three social files, and spot-check `email_preview_DATE.txt` for the stale title too.
