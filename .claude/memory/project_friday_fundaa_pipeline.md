---
name: friday-fundaa-publish-status-and-pipeline
description: Publish status table by date/topic and the publish steps for the Friday Fundaa article series
metadata: 
  node_type: memory
  type: project
  originSessionId: e03b998a-3cab-497f-abac-389a5dd8f548
  modified: 2026-07-25T11:38:51.232Z
---

| Date | Topic | Status |
|------|-------|--------|
| 2026-03-13 | Shrinkflation | Live |
| 2026-03-20 | Stagflation | Live |
| 2026-03-27 | Yield curve | Written, not yet published |
| 2026-03-28 | WTI & Brent crude | Written, not yet published |
| 2026-04-04 | Tariffs (who actually pays?) | Written, not yet published |

Source files: `weekly-newsletter/content/articles/friday-fundaa-*.md`.

To publish: run `build_combined_site.py`, commit `site/fundaa/YYYY-MM-DD/` +
`site/index.html`, push.
