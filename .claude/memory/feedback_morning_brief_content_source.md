---
name: Approved MD is the content source — no regeneration after approval
description: Once any edition markdown is reviewed and approved, use it as the single source of truth. Never regenerate content. Never touch previously published editions.
type: feedback
---

Once a markdown draft is generated and the user has reviewed and approved it, that file is the authoritative content source for all downstream outputs. This applies to:

- **Morning Brief** (daily)
- **Global Investor Edition** (weekly, published Saturday)
- Any other edition once the user has approved the content

Downstream outputs built from the approved MD:
- Web HTML
- Email HTML
- Social media (LinkedIn, X/Twitter)

**Why:** Avoids narrative drift between channels — the approved text is what the user signed off on, not a re-generated variant. Re-running generators (e.g. `generate_global_newsletter.py` via `publish_weekly.sh`) will overwrite manual edits with a new Claude API call, losing all approved changes.

**How to apply:**
- Parse and reuse the approved `.md` file when building web/email/social content.
- Do NOT call the Claude API again to rewrite or regenerate narrative sections.
- Do NOT re-run generators (`generate_global_newsletter.py`, `generate_newsletter.py`, etc.) after the user approves content — run `build_combined_site.py` directly instead.
- Only format/adapt layout as needed for each channel.

**Permanent code enforcement (added 2026-03-30):**
- `publish_daybreak.sh --publish` now hard-errors if the approved MD doesn't exist — it will NEVER generate content or call Claude when publishing to web.
- `generate_market_day_break.py --no-rewrite-md` now calls `_override_from_approved_md()` before building social posts, so LinkedIn/X/Substack content comes from the approved MD, not empty strings.
- `build_combined_site.py` already calls `build_daybreak_context(use_claude=False)` + `_override_ctx_from_approved_md()` — no Claude call during site build.

**Previous editions:**
- Never regenerate or modify content for previously published editions.
- Before any action that could affect a past edition, ask the user explicitly to confirm.
