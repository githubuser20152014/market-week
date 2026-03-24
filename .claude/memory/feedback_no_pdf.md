---
name: No PDF for Daybreak
description: PDF generation is not needed for the Market Day Break daily edition
type: feedback
---

Do not generate a PDF for the Market Day Break daily edition.

**Why:** User confirmed PDFs are not needed — the publish workflow should skip the PDF step entirely.

**How to apply:** When running `publish_daybreak.sh` or manually publishing a daybreak edition, do not run `--pdf` or any PDF generation step. If `verify_site_content.py` fails because a PDF is missing, that check can be ignored or bypassed — it's not a blocking issue.
