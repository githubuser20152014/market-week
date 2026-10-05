---
name: Past editions — confirm before touching
description: Always ask user before making changes that affect previously published daily editions
type: feedback
---

Before applying any change that would affect past (already-published) daily editions — including site rebuilds, HTML updates, backfills, or fixes — ask the user explicitly:
"Would you like to apply this to past editions too, or just going forward?"

Wait for confirmation before touching historical content.

**Why:** User wants full control over what gets changed in the archive. Changes to past editions should be intentional, not a side effect of a fix or workflow improvement.

**How to apply:** Applies to any script, site rebuild, or code change that iterates over `daybreak_dates`, `find_daybreak_dates()`, or otherwise touches `site/daily/*/` for dates before today.
