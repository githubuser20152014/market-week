---
name: Daybreak distribution — Substack note first
description: Substack note is published before X and LinkedIn; X/LinkedIn link to Substack, not frameworkfoundry.info
type: feedback
---

Publish the Substack note first. X and LinkedIn then point readers to the Substack note, not to the Framework Foundry site.

**Why:** X and LinkedIn readers should land on Substack to build that audience. The site is the archive; Substack is the daily destination.

**How to apply:**
1. After `--publish`, open `output/substack_DATE.html`, paste into Substack editor, publish.
2. Copy the live Substack note URL.
3. In `output/x_DATE.txt` and `output/linkedin_DATE.txt`, replace the default `frameworkfoundry.info/daily/DATE/` link with the Substack note URL.
4. CTA text is "Read on Substack:" (X) / "Read on Substack →" (LinkedIn). Never "Full breakdown" — the note IS the content, not a pointer to more.

The generator defaults to `frameworkfoundry.info` because the Substack URL isn't known until after publishing. The URL swap is always a manual step.
