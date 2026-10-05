---
name: LinkedIn posts — update Substack link
description: Replace generated Substack URLs in LinkedIn posts with frameworkfoundrymkt.substack.com
type: feedback
---

**Rule:** In LinkedIn posts for Daybreak, replace the auto-generated Substack URL with `frameworkfoundrymkt.substack.com`.

**Why:** The Substack publication URL is the stable, canonical link for subscribers and is more brand-recognizable than frameworkfoundry.info.

**How to apply:** After `publish_daybreak.sh --publish` generates `output/linkedin_YYYY-MM-DD.txt`, open the file and replace any Substack note URL (e.g., `https://frameworkfoundrymkt.substack.com/p/...`) with the root domain `frameworkfoundrymkt.substack.com`. CTA remains "Read on Substack".
