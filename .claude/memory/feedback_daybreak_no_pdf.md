---
name: No PDF for Daybreak editions
description: Skip PDF generation for daily Market Day Break edition
type: feedback
---

**Rule:** Do not generate PDF for Daybreak daily edition.

**Why:** PDF adds no value for daily ephemeral content; web + email + social are the distribution channels.

**How to apply:** When running `publish_daybreak.sh --publish`, the script does not generate PDF by default. If a future script version adds `--pdf` flag, do not use it for Daybreak runs.
